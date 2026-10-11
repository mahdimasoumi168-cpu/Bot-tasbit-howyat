"""Variza payment-link creation and signed webhook processing."""

import hashlib
import hmac
import json
import logging
import re
from datetime import datetime
from urllib.parse import urlparse

from aiohttp import ClientSession, ClientTimeout, web
from sqlalchemy import select, update

from app.core.config import get_settings
from app.db.models import (
    AuditLog, DiscountCode, Order, Payment, Service, User, Wallet, WalletTopup, WalletTransaction,
)
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


class _ConcurrentDelivery(Exception):
    """A concurrent webhook already changed the payment/order state."""


async def create_payment_link(
    api_key: str, amount_toman: int, title: str, return_url: str
) -> tuple[str, str]:
    """Create a Variza payment link and return (pay_url, slug)."""
    if not api_key:
        raise RuntimeError("VARIZA_API_KEY تنظیم نشده است.")
    if amount_toman < 1000:
        raise ValueError("مبلغ پرداخت آنلاین باید حداقل ۱۰۰۰ تومان باشد.")
    parsed_return = urlparse(return_url)
    if parsed_return.scheme != "https" or not parsed_return.netloc:
        raise ValueError("PUBLIC_BASE_URL باید یک نشانی عمومی HTTPS باشد.")

    timeout = ClientTimeout(total=20)
    async with ClientSession(timeout=timeout) as client:
        async with client.post(
            "https://variza.ir/api/v1/pay",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "amount": amount_toman,
                "return_url": return_url,
                "title": title[:120],
                "expires_in": "1h",
            },
        ) as response:
            if response.status not in (200, 201):
                logger.warning("Variza payment-link API returned HTTP %s", response.status)
                raise RuntimeError("واریزا نتوانست لینک پرداخت را بسازد؛ تنظیمات API و اعتبار حساب را بررسی کنید.")
            try:
                body = await response.json(content_type=None)
            except (ValueError, json.JSONDecodeError) as exc:
                raise RuntimeError("پاسخ واریزا قابل خواندن نیست.") from exc

    pay_url = body.get("pay_url") if isinstance(body, dict) else None
    if not isinstance(pay_url, str):
        raise RuntimeError("واریزا در پاسخ خود لینک پرداخت معتبر برنگرداند.")
    parsed_pay = urlparse(pay_url)
    if parsed_pay.scheme != "https" or parsed_pay.hostname != "variza.ir" or not parsed_pay.path.startswith("/pay/"):
        raise RuntimeError("نشانی پرداخت برگشتی از واریزا معتبر نیست.")
    slug = body.get("slug") or parsed_pay.path.rstrip("/").split("/")[-1]
    if not isinstance(slug, str) or not re.fullmatch(r"[A-Za-z0-9_-]{4,128}", slug):
        raise RuntimeError("شناسه لینک پرداخت واریزا معتبر نیست.")
    return pay_url, slug


def verify_webhook_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    """Verify Variza's HMAC-SHA256 signature against the exact raw request body."""
    if not secret or not signature:
        return False
    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature.strip())


async def handle_variza_webhook(request: web.Request, bot) -> web.Response:
    settings = get_settings()
    if not settings.variza_webhook_secret:
        return web.json_response({"ok": False, "error": "webhook_not_configured"}, status=503)

    raw_body = await request.read()
    signature = request.headers.get("X-Webhook-Signature", "")
    if not verify_webhook_signature(raw_body, signature, settings.variza_webhook_secret):
        logger.warning("Rejected Variza webhook with invalid signature")
        return web.json_response({"ok": False, "error": "invalid_signature"}, status=400)

    try:
        payload = json.loads(raw_body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return web.json_response({"ok": False, "error": "invalid_json"}, status=400)

    if not isinstance(payload, dict):
        return web.json_response({"ok": False, "error": "invalid_payload"}, status=400)
    if payload.get("event") != "payment.paid" or payload.get("status") != "paid":
        return web.json_response({"ok": True, "ignored": True})

    slug = payload.get("slug")
    try:
        base_amount = int(payload.get("base_amount", payload.get("amount", 0)))
    except (TypeError, ValueError):
        return web.json_response({"ok": False, "error": "invalid_amount"}, status=400)
    if not isinstance(slug, str) or not slug or base_amount < 1000:
        return web.json_response({"ok": False, "error": "invalid_payment"}, status=400)

    outcome = "unknown"
    order_id = None
    telegram_id = None
    public_id = None
    service_name = None
    try:
        async with SessionLocal() as session:
            async with session.begin():
                # Wallet top-ups use WalletTopup.receipt_file_id to retain the
                # provider slug; no schema migration is needed for existing databases.
                topup_row = (
                    await session.execute(
                        select(WalletTopup, User)
                        .join(User, WalletTopup.user_id == User.id)
                        .where(
                            WalletTopup.receipt_type == "variza",
                            WalletTopup.receipt_file_id == slug,
                        )
                    )
                ).one_or_none()

                if topup_row is not None:
                    topup, user = topup_row
                    telegram_id = user.telegram_id
                    topup_id = topup.id
                    if topup.status == "paid":
                        outcome = "duplicate"
                    elif topup.status != "waiting_online_payment":
                        outcome = "ignored"
                    elif int(topup.amount_toman) != base_amount:
                        logger.error(
                            "Variza amount mismatch for wallet top-up %s (expected %s, received %s)",
                            topup.id, topup.amount_toman, base_amount,
                        )
                        outcome = "amount_mismatch"
                    else:
                        topup_update = await session.execute(
                            update(WalletTopup)
                            .where(
                                WalletTopup.id == topup.id,
                                WalletTopup.status == "waiting_online_payment",
                            )
                            .values(status="paid", reviewed_at=datetime.now())
                        )
                        if topup_update.rowcount != 1:
                            raise _ConcurrentDelivery()

                        wallet = (
                            await session.execute(
                                select(Wallet).where(Wallet.user_id == user.id)
                            )
                        ).scalar_one_or_none()
                        if wallet is None:
                            wallet = Wallet(user_id=user.id, balance_toman=0)
                            session.add(wallet)
                            await session.flush()
                        wallet.balance_toman += base_amount
                        session.add(
                            WalletTransaction(
                                user_id=user.id,
                                amount_toman=base_amount,
                                balance_after_toman=wallet.balance_toman,
                                kind="topup",
                                description=f"افزایش اعتبار آنلاین واریزا #{topup.id}",
                                order_id=None,
                                topup_id=topup.id,
                            )
                        )
                        session.add(
                            AuditLog(
                                actor_telegram_id=None,
                                action="variza_wallet_topup",
                                order_id=None,
                                details_json=json.dumps(
                                    {
                                        "slug": slug,
                                        "topup_id": topup.id,
                                        "amount_toman": base_amount,
                                        "attempt_code": str(payload.get("attempt_code", ""))[:128],
                                    },
                                    ensure_ascii=False,
                                ),
                            )
                        )
                        outcome = "wallet_approved"
                else:
                    row = (
                        await session.execute(
                            select(Payment, Order, User, Service)
                            .join(Order, Payment.order_id == Order.id)
                            .join(User, Order.user_id == User.id)
                            .join(Service, Order.service_id == Service.id)
                            .where(
                                Payment.receipt_type == "variza",
                                Payment.receipt_file_id == slug,
                            )
                        )
                    ).one_or_none()

                    if row is None:
                        outcome = "unknown"
                    else:
                        payment, order, user, service = row
                        order_id = order.id
                        telegram_id = user.telegram_id
                        public_id = order.public_id
                        service_name = service.name

                        if payment.status == "approved" or order.status in {
                            "payment_approved", "in_progress", "waiting_user", "completed"
                        }:
                            outcome = "duplicate"
                        elif payment.status != "pending" or order.status != "waiting_payment":
                            outcome = "ignored"
                        elif int(payment.amount_toman) != base_amount:
                            logger.error(
                                "Variza amount mismatch for order %s (expected %s, received base %s)",
                                order.public_id, payment.amount_toman, base_amount,
                            )
                            outcome = "amount_mismatch"
                        else:
                            payment_update = await session.execute(
                                update(Payment)
                                .where(Payment.id == payment.id, Payment.status == "pending")
                                .values(status="approved")
                            )
                            order_update = await session.execute(
                                update(Order)
                                .where(Order.id == order.id, Order.status == "waiting_payment")
                                .values(status="payment_approved")
                            )
                            if payment_update.rowcount != 1 or order_update.rowcount != 1:
                                raise _ConcurrentDelivery()

                            data = json.loads(order.data_json or "{}")
                            coupon_code = data.get("discount_code")
                            if coupon_code:
                                coupon = (
                                    await session.execute(
                                        select(DiscountCode).where(DiscountCode.code == coupon_code)
                                    )
                                ).scalar_one_or_none()
                                if coupon is not None:
                                    coupon.used_count += 1

                            session.add(
                                AuditLog(
                                    actor_telegram_id=None,
                                    action="variza_payment",
                                    order_id=order.id,
                                    details_json=json.dumps(
                                        {
                                            "slug": slug,
                                            "amount_toman": base_amount,
                                            "attempt_code": str(payload.get("attempt_code", ""))[:128],
                                        },
                                        ensure_ascii=False,
                                    ),
                                )
                            )
                            outcome = "approved"
    except _ConcurrentDelivery:
        outcome = "duplicate"
    except Exception:
        logger.exception("Error while processing a signed Variza webhook")
        return web.json_response({"ok": False, "error": "processing_failed"}, status=500)

    if outcome == "unknown":
        logger.warning("Received Variza webhook for an unknown payment slug")
        return web.json_response({"ok": False, "error": "unknown_payment"}, status=404)
    if outcome == "wallet_approved":
        try:
            await bot.send_message(
                telegram_id,
                "✅ پرداخت افزایش اعتبار با موفقیت تأیید شد.\n\n"
                f"💰 مبلغ افزوده‌شده: {base_amount:,} تومان\n"
                f"🧾 شماره شارژ: #{topup_id}\n"
                "موجودی کیف پول شما به‌روزرسانی شد.",
            )
        except Exception:
            logger.exception("Wallet top-up was recorded but user notification failed")
        for admin_id in settings.admin_id_set:
            try:
                await bot.send_message(
                    admin_id,
                    "💳 افزایش اعتبار آنلاین واریزا تأیید شد.\n"
                    f"شناسه مشترک: {telegram_id}\nشماره شارژ: #{topup_id}\n"
                    f"مبلغ: {base_amount:,} تومان",
                )
            except Exception:
                logger.exception("Wallet top-up was recorded but admin notification failed")
        return web.json_response({"ok": True, "result": "wallet_approved"})
    if outcome != "approved":
        # A valid, already-handled delivery or a superseded/mismatched payment should not retry forever.
        return web.json_response({"ok": True, "result": outcome})

    try:
        await bot.send_message(
            telegram_id,
            f"✅ پرداخت آنلاین شما با موفقیت تأیید شد.\n\n"
            f"📋 شماره درخواست: {public_id}\n"
            f"🧾 خدمت: {service_name}\n"
            f"💰 مبلغ: {base_amount:,} تومان\n\n"
            "پرونده برای انجام خدمت به اپراتورهای مجاز ارسال شد.",
        )
    except Exception:
        logger.exception("Payment was recorded but user Telegram notification failed")

    try:
        from app.bot.admin import send_case_to_operator
        await send_case_to_operator(bot, order_id)
    except Exception:
        logger.exception("Payment was recorded but operator notification failed")

    for admin_id in settings.admin_id_set:
        try:
            await bot.send_message(
                admin_id,
                f"💳 پرداخت آنلاین واریزا تأیید شد.\n"
                f"شماره درخواست: {public_id}\nمبلغ: {base_amount:,} تومان",
            )
        except Exception:
            logger.exception("Payment was recorded but admin notification failed")

    return web.json_response({"ok": True, "result": "approved"})


def create_web_app(bot) -> web.Application:
    app = web.Application(client_max_size=64 * 1024)

    async def health(_request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    async def payment_return(_request: web.Request) -> web.Response:
        return web.Response(
            text=(
                "<!doctype html><html lang='fa' dir='rtl'><meta charset='utf-8'>"
                "<meta name='viewport' content='width=device-width, initial-scale=1'>"
                "<title>کمک‌یار مهاجر</title><body style='font-family:sans-serif;padding:2rem'>"
                "<h2>درخواست پرداخت شما دریافت شد</h2>"
                "<p>برای مشاهده وضعیت نهایی، به ربات تلگرام «کمک‌یار مهاجر» برگردید. "
                "وضعیت پرداخت فقط پس از تأیید امن واریزا به‌روزرسانی می‌شود.</p>"
                "</body></html>"
            ),
            content_type="text/html",
        )

    async def webhook(request: web.Request) -> web.Response:
        return await handle_variza_webhook(request, bot)

    app.router.add_get("/health", health)
    app.router.add_get("/payments/return", payment_return)
    app.router.add_post("/webhooks/variza", webhook)
    return app
