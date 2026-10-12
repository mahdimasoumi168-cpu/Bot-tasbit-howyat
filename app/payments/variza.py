"""Variza payment-link creation and signed webhook processing."""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from typing import Any

import aiohttp
from sqlalchemy import select, update

from app.core.config import get_settings
from app.db.models import (
    DiscountCode,
    Order,
    Payment,
    Service,
    User,
    VarizaPayment,
    Wallet,
    WalletTopup,
    WalletTransaction,
)
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)
VARIZA_PAY_URL = "https://variza.ir/api/v1/pay"


class VarizaError(RuntimeError):
    """A safe, user-displayable Variza integration error."""


def verify_webhook_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    if not secret or not signature:
        return False
    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature.strip())


def _parse_expiry(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed
    except (TypeError, ValueError):
        return None


def _public_base_url() -> str:
    settings = get_settings()
    base = settings.public_base_url.strip().rstrip("/") or "https://bot-tasbit-howyat-production.up.railway.app"
    if not base.startswith("https://"):
        raise VarizaError(
            "آدرس عمومی ربات باید با https شروع شود؛ متغیر PUBLIC_BASE_URL را بررسی کنید."
        )
    return base


async def create_variza_link(
    *,
    kind: str,
    user_id: int,
    amount_toman: int,
    title: str,
    order_id: int | None = None,
    topup_id: int | None = None,
) -> str:
    """Create or reuse a live link and persist its exact amount and owner."""
    if kind not in {"order", "topup"}:
        raise VarizaError("نوع پرداخت معتبر نیست.")
    if amount_toman < 1000:
        raise VarizaError(
            "حداقل مبلغ ساخت لینک واریزا ۱٬۰۰۰ تومان است؛ لطفاً کارت‌به‌کارت را انتخاب کنید."
        )
    settings = get_settings()
    if not settings.variza_api_key.strip() or not settings.variza_webhook_secret.strip():
        raise VarizaError(
            "اتصال واریزا کامل تنظیم نشده است؛ لطفاً از کارت‌به‌کارت استفاده کنید یا با پشتیبانی تماس بگیرید."
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    async with SessionLocal() as session:
        query = select(VarizaPayment).where(
            VarizaPayment.kind == kind,
            VarizaPayment.status == "pending",
            VarizaPayment.expires_at > now,
        )
        if kind == "order":
            query = query.where(VarizaPayment.order_id == order_id)
        else:
            query = query.where(VarizaPayment.topup_id == topup_id)
        existing = (await session.execute(query.order_by(VarizaPayment.created_at.desc()))).scalars().first()
        if existing and existing.pay_url and existing.amount_toman == amount_toman:
            return existing.pay_url

    return_url = _public_base_url() + "/payments/variza/return"
    payload = {
        "amount": amount_toman,
        "return_url": return_url,
        "title": title[:180],
        "expires_in": "1h",
    }
    timeout = aiohttp.ClientTimeout(total=20)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as client:
            async with client.post(
                VARIZA_PAY_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.variza_api_key}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
            ) as response:
                raw_text = await response.text()
                try:
                    parsed_body = json.loads(raw_text)
                    body: dict[str, Any] = parsed_body if isinstance(parsed_body, dict) else {}
                except (json.JSONDecodeError, TypeError):
                    body = {}
                if response.status not in {200, 201}:
                    detail = (
                        body.get("detail")
                        or body.get("message")
                        or body.get("error")
                        or body.get("errors")
                    )
                    if isinstance(detail, (dict, list)):
                        detail = json.dumps(detail, ensure_ascii=False)
                    if response.status == 401:
                        message = "کلید API واریزا معتبر نیست؛ متغیر VARIZA_API_KEY را بررسی کنید."
                    elif response.status == 422:
                        message = (
                            "واریزا لینک پرداخت را نساخت (خطای ۴۲۲). در پنل واریزا بررسی کنید "
                            "که callback_url ثبت باشد، پلن اجازه لینک فعال جدید بدهد و کارت مقصد فعال باشد."
                        )
                    elif response.status == 429:
                        message = "تعداد درخواست‌های واریزا بیش از حد مجاز است؛ کمی بعد دوباره تلاش کنید."
                    else:
                        message = f"ساخت لینک واریزا ناموفق بود (HTTP {response.status})."
                    if detail:
                        message += f" جزئیات: {str(detail)[:400]}"
                    raise VarizaError(message)
    except aiohttp.ClientError as exc:
        logger.warning("Variza payment-link request failed: %s", type(exc).__name__)
        raise VarizaError(
            "ارتباط با واریزا برقرار نشد؛ لطفاً کمی بعد دوباره تلاش کنید یا کارت‌به‌کارت را انتخاب کنید."
        ) from exc

    slug = str(body.get("slug") or "").strip()
    pay_url = str(body.get("pay_url") or "").strip()
    if not slug or not pay_url.startswith("https://variza.ir/"):
        logger.warning("Variza returned an incomplete payment-link response")
        raise VarizaError("واریزا پاسخ معتبر برای لینک پرداخت برنگرداند؛ لطفاً دوباره تلاش کنید.")
    expiry = _parse_expiry(body.get("expires_at"))

    async with SessionLocal() as session:
        record = VarizaPayment(
            slug=slug,
            kind=kind,
            order_id=order_id,
            topup_id=topup_id,
            user_id=user_id,
            amount_toman=amount_toman,
            pay_url=pay_url,
            status="pending",
            expires_at=expiry,
        )
        session.add(record)
        await session.commit()
    return pay_url


async def process_webhook(raw_body: bytes, signature: str) -> tuple[int, dict[str, Any]]:
    """Validate and process one Variza event exactly once."""
    settings = get_settings()
    if not settings.variza_webhook_secret:
        return 503, {"ok": False, "error": "webhook_secret_missing"}
    if not verify_webhook_signature(raw_body, signature, settings.variza_webhook_secret):
        return 401, {"ok": False, "error": "invalid_signature"}
    try:
        event = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return 400, {"ok": False, "error": "invalid_json"}
    if not isinstance(event, dict):
        return 400, {"ok": False, "error": "invalid_json"}
    if event.get("event") != "payment.paid" or event.get("status") != "paid":
        return 200, {"ok": True, "action": "ignored_event"}

    slug = str(event.get("slug") or "").strip()
    attempt_code = str(event.get("attempt_code") or "").strip() or None
    try:
        base_amount = int(event.get("base_amount", event.get("amount")))
    except (TypeError, ValueError):
        return 400, {"ok": False, "error": "invalid_amount"}
    if not slug or base_amount <= 0:
        return 400, {"ok": False, "error": "missing_payment_fields"}

    async with SessionLocal() as session:
        record = (
            await session.execute(select(VarizaPayment).where(VarizaPayment.slug == slug))
        ).scalar_one_or_none()
        if record is None:
            logger.warning("Received signed Variza webhook for unknown slug")
            return 404, {"ok": False, "error": "unknown_payment"}
        if record.status == "paid":
            return 200, {"ok": True, "action": "duplicate"}
        if record.status != "pending":
            return 200, {"ok": True, "action": "already_handled"}
        if base_amount != record.amount_toman:
            logger.error("Variza amount mismatch for stored payment id=%s", record.id)
            return 400, {"ok": False, "error": "amount_mismatch"}

        if attempt_code:
            reused = (
                await session.execute(
                    select(VarizaPayment).where(
                        VarizaPayment.attempt_code == attempt_code,
                        VarizaPayment.status == "paid",
                    )
                )
            ).scalar_one_or_none()
            if reused:
                record.status = "ignored"
                await session.commit()
                return 200, {"ok": True, "action": "duplicate_attempt"}

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if record.kind == "order":
            order = await session.get(Order, record.order_id)
            if order is None:
                return 404, {"ok": False, "error": "order_not_found"}
            claim = await session.execute(
                update(Order)
                .where(
                    Order.id == order.id,
                    Order.status.in_(["waiting_payment", "waiting_receipt_review"]),
                )
                .values(status="payment_approved")
            )
            if claim.rowcount != 1:
                record.status = "ignored"
                record.attempt_code = attempt_code
                await session.commit()
                return 200, {
                    "ok": True,
                    "action": "already_paid",
                    "order_id": order.id,
                    "amount_toman": record.amount_toman,
                }
            service = await session.get(Service, order.service_id)
            user = await session.get(User, record.user_id)
            record.status = "paid"
            record.attempt_code = attempt_code
            record.paid_at = now
            session.add(
                Payment(
                    order_id=order.id,
                    amount_toman=record.amount_toman,
                    receipt_file_id=None,
                    receipt_type="variza",
                    status="approved",
                )
            )
            order_data = json.loads(order.data_json or "{}")
            coupon_code = order_data.get("discount_code")
            if coupon_code:
                coupon = (
                    await session.execute(
                        select(DiscountCode).where(DiscountCode.code == coupon_code)
                    )
                ).scalar_one_or_none()
                if coupon and (
                    coupon.max_uses is None or coupon.used_count < coupon.max_uses
                ):
                    coupon.used_count += 1
            await session.commit()
            return 200, {
                "ok": True,
                "action": "paid_order",
                "order_id": order.id,
                "public_id": order.public_id,
                "service_name": service.name if service else "خدمت",
                "user_telegram_id": user.telegram_id if user else None,
                "amount_toman": record.amount_toman,
            }

        topup = await session.get(WalletTopup, record.topup_id)
        if topup is None:
            return 404, {"ok": False, "error": "topup_not_found"}
        claim = await session.execute(
            update(WalletTopup)
            .where(
                WalletTopup.id == topup.id,
                WalletTopup.status.in_(["awaiting_receipt", "waiting_receipt_review"]),
            )
            .values(status="approved", reviewed_at=now)
        )
        if claim.rowcount != 1:
            record.status = "ignored"
            record.attempt_code = attempt_code
            await session.commit()
            return 200, {
                "ok": True,
                "action": "already_paid",
                "topup_id": topup.id,
                "amount_toman": record.amount_toman,
            }

        wallet = (
            await session.execute(select(Wallet).where(Wallet.user_id == topup.user_id))
        ).scalar_one_or_none()
        if wallet is None:
            wallet = Wallet(user_id=topup.user_id, balance_toman=0)
            session.add(wallet)
            await session.flush()
        await session.execute(
            update(Wallet)
            .where(Wallet.user_id == topup.user_id)
            .values(balance_toman=Wallet.balance_toman + record.amount_toman)
        )
        await session.refresh(wallet)
        user = await session.get(User, topup.user_id)
        record.status = "paid"
        record.attempt_code = attempt_code
        record.paid_at = now
        session.add(
            WalletTransaction(
                user_id=topup.user_id,
                amount_toman=record.amount_toman,
                balance_after_toman=wallet.balance_toman,
                kind="topup",
                description=f"افزایش اعتبار واریزا #{topup.id}",
                topup_id=topup.id,
            )
        )
        await session.commit()
        return 200, {
            "ok": True,
            "action": "paid_topup",
            "topup_id": topup.id,
            "user_telegram_id": user.telegram_id if user else None,
            "amount_toman": record.amount_toman,
            "new_balance_toman": wallet.balance_toman,
        }
