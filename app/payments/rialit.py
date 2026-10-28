"""Rialit Pay link creation and server-side payment verification."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import aiohttp
from sqlalchemy import select, update

from app.core.config import get_settings
from app.db.models import (
    Order, Payment, RialitPayment, Service, User, Wallet, WalletTopup, WalletTransaction
)
from app.db.session import SessionLocal
from app.payments.gozarban import GozarbanError, ensure_vpn_subscription

logger = logging.getLogger(__name__)
API_ROOT = "https://api.rialit.org/api/v1"


class RialitError(RuntimeError):
    """Safe payment error suitable for displaying to the user."""


def _base_url() -> str:
    base = get_settings().public_base_url.strip().rstrip("/")
    if not base.startswith("https://"):
        raise RialitError("آدرس عمومی ربات معتبر نیست؛ تنظیم PUBLIC_BASE_URL را بررسی کنید.")
    return base


async def create_rialit_link(*, kind: str, user_id: int, amount_toman: int,
                             title: str, order_id: int | None = None,
                             topup_id: int | None = None,
                             vpn_months: int | None = None,
                             vpn_gigabytes: int | None = None) -> str:
    if kind not in {"order", "topup", "vpn"} or amount_toman <= 0:
        raise RialitError("اطلاعات پرداخت معتبر نیست.")
    if kind == "vpn" and (vpn_months not in (1, 2, 3, 4) or vpn_gigabytes not in range(10, 101, 10)):
        raise RialitError("بسته VPN معتبر نیست.")
    settings = get_settings()
    api_key = settings.rialit_api_key.strip()
    if not api_key:
        raise RialitError("کلید اتصال ریالیت تنظیم نشده است؛ با پشتیبانی تماس بگیرید.")
    async with SessionLocal() as session:
        q = select(RialitPayment).where(
            RialitPayment.kind == kind, RialitPayment.status == "pending",
            RialitPayment.amount_toman == amount_toman
        )
        if kind == "order":
            q = q.where(RialitPayment.order_id == order_id)
        elif kind == "topup":
            q = q.where(RialitPayment.topup_id == topup_id)
        else:
            q = q.where(RialitPayment.vpn_months == vpn_months,
                         RialitPayment.vpn_gigabytes == vpn_gigabytes,
                         RialitPayment.user_id == user_id)
        existing = (await session.execute(q.order_by(RialitPayment.id.desc()))).scalars().first()
        if existing and existing.pay_url:
            return existing.pay_url
    payload = {
        "amount": amount_toman,
        "callback_url": _base_url() + "/webhooks/rialit",
        "order_id": f"{kind}-{order_id if kind == 'order' else topup_id if kind == 'topup' else f'{user_id}-{vpn_months}-{vpn_gigabytes}'}-{int(datetime.now(timezone.utc).timestamp())}",
        "user_id": int(user_id),
    }
    timeout = aiohttp.ClientTimeout(total=25)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as client:
            async with client.post(
                f"{API_ROOT}/send", json=payload,
                headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
            ) as response:
                raw = await response.text()
                try:
                    body = json.loads(raw)
                except json.JSONDecodeError:
                    body = {}
                if response.status not in (200, 201) or not isinstance(body, dict):
                    logger.warning("Rialit link creation failed HTTP %s", response.status)
                    raise RialitError(f"ساخت لینک ریالیت ناموفق بود (HTTP {response.status}).")
    except aiohttp.ClientError as exc:
        logger.warning("Rialit request failed: %s", type(exc).__name__)
        raise RialitError("ارتباط با درگاه ریالیت برقرار نشد؛ کمی بعد دوباره تلاش کنید.") from exc
    nested = body.get("data") if isinstance(body.get("data"), dict) else {}
    token = str(body.get("token") or nested.get("token") or "").strip()
    if not token or len(token) > 64 or any(ch in token for ch in "/?#"):
        raise RialitError("پاسخ درگاه ریالیت برای ساخت لینک معتبر نبود.")
    pay_url = f"{API_ROOT}/redirect/{token}"
    async with SessionLocal() as session:
        session.add(RialitPayment(
            token=token, kind=kind, order_id=order_id, topup_id=topup_id,
            user_id=user_id, amount_toman=amount_toman,
            vpn_months=vpn_months if kind == "vpn" else None,
            vpn_gigabytes=vpn_gigabytes if kind == "vpn" else None,
            pay_url=pay_url, status="pending"
        ))
        await session.commit()
    return pay_url


async def _provision_paid_vpn(
    *, payment_id: int, user_telegram_id: int | None, amount_toman: int,
    months: int | None, gigabytes: int | None,
) -> tuple[int, dict[str, Any]]:
    base = {
        "user_telegram_id": user_telegram_id,
        "amount_toman": amount_toman,
        "months": months,
        "gigabytes": gigabytes,
    }
    if not user_telegram_id or not months or not gigabytes:
        return 200, {"ok": True, "action": "paid_vpn_pending",
                     **base, "reason": "اطلاعات مشترک یا سفارش ناقص است."}
    try:
        provisioned = await ensure_vpn_subscription(
            payment_id=payment_id,
            telegram_user_id=user_telegram_id,
            gigabytes=gigabytes,
            months=months,
        )
    except GozarbanError as exc:
        logger.warning("Gozarban provisioning pending for Rialit payment id=%s: %s",
                       payment_id, str(exc))
        return 200, {"ok": True, "action": "paid_vpn_pending",
                     **base, "reason": str(exc)}
    except Exception:
        logger.exception("Gozarban provisioning failed for Rialit payment id=%s", payment_id)
        return 200, {"ok": True, "action": "paid_vpn_pending",
                     **base, "reason": "اتصال به گذربان موقتاً ناموفق بود؛ دوباره تلاش می‌شود."}
    return 200, {"ok": True, "action": "paid_vpn",
                 **base, "subscription_url": provisioned.get("subscription_url"),
                 "subscription_id": provisioned.get("subscription_id"),
                 "username": provisioned.get("username"),
                 "already_existed": provisioned.get("already_existed", False)}


async def process_rialit_webhook(payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Never trust callback parameters as proof; query Rialit verify API."""
    token = str(payload.get("token") or payload.get("payment_token") or "").strip()
    if not token:
        return 400, {"ok": False, "error": "missing_token"}
    settings = get_settings()
    api_key = settings.rialit_api_key.strip()
    if not api_key:
        return 503, {"ok": False, "error": "gateway_not_configured"}
    already_paid_vpn: dict[str, Any] | None = None
    async with SessionLocal() as session:
        payment = (await session.execute(
            select(RialitPayment).where(RialitPayment.token == token)
        )).scalar_one_or_none()
        if payment is None:
            return 404, {"ok": False, "error": "unknown_payment"}
        if payment.status == "paid":
            if payment.kind != "vpn":
                return 200, {"ok": True, "action": "duplicate"}
            user = await session.get(User, payment.user_id)
            already_paid_vpn = {
                "payment_id": payment.id,
                "user_telegram_id": user.telegram_id if user else None,
                "amount_toman": payment.amount_toman,
                "months": payment.vpn_months,
                "gigabytes": payment.vpn_gigabytes,
            }
        expected_amount = payment.amount_toman
        payment_id = payment.id
    if already_paid_vpn is not None:
        return await _provision_paid_vpn(**already_paid_vpn)
    timeout = aiohttp.ClientTimeout(total=25)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as client:
            async with client.post(
                f"{API_ROOT}/verify/{token}",
                headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
            ) as response:
                raw = await response.text()
                try:
                    verified = json.loads(raw)
                except json.JSONDecodeError:
                    verified = {}
                if response.status == 409:
                    return 202, {"ok": True, "action": "pending"}
                if response.status != 200 or not isinstance(verified, dict):
                    logger.warning("Rialit verify returned HTTP %s", response.status)
                    return 502, {"ok": False, "error": "verification_unavailable"}
    except aiohttp.ClientError as exc:
        logger.warning("Rialit verify request failed: %s", type(exc).__name__)
        return 502, {"ok": False, "error": "verification_unavailable"}
    data = verified.get("data") if isinstance(verified.get("data"), dict) else verified
    try:
        status = int(data.get("status"))
    except (TypeError, ValueError):
        return 502, {"ok": False, "error": "invalid_verification_response"}
    if status == 4:
        async with SessionLocal() as session:
            row = await session.get(RialitPayment, payment_id)
            if row and row.status == "pending":
                row.status = "failed"
                await session.commit()
        return 200, {"ok": True, "action": "failed"}
    if status != 3:
        return 202, {"ok": True, "action": "pending"}
    try:
        verified_amount_raw = data.get("amount", data.get("paid_amount"))
        if verified_amount_raw is None:
            return 502, {"ok": False, "error": "verified_amount_missing"}
        verified_amount = int(verified_amount_raw)
    except (TypeError, ValueError):
        return 400, {"ok": False, "error": "invalid_verified_amount"}
    if verified_amount != expected_amount:
        logger.error("Rialit verified amount mismatch for payment id=%s", payment_id)
        return 400, {"ok": False, "error": "amount_mismatch"}

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    async with SessionLocal() as session:
        record = await session.get(RialitPayment, payment_id)
        if not record or record.status == "paid":
            return 200, {"ok": True, "action": "duplicate"}
        if record.status != "pending":
            return 200, {"ok": True, "action": "already_handled"}
        if record.kind == "vpn":
            user = await session.get(User, record.user_id)
            record.status, record.paid_at = "paid", now
            await session.commit()
            return await _provision_paid_vpn(
                payment_id=record.id,
                user_telegram_id=user.telegram_id if user else None,
                amount_toman=record.amount_toman,
                months=record.vpn_months,
                gigabytes=record.vpn_gigabytes,
            )
        if record.kind == "order":
            claim = await session.execute(update(Order).where(
                Order.id == record.order_id,
                Order.status.in_(["waiting_payment", "waiting_receipt_review"])
            ).values(status="payment_approved"))
            if claim.rowcount != 1:
                record.status = "ignored"
                await session.commit()
                return 200, {"ok": True, "action": "already_paid"}
            order = await session.get(Order, record.order_id)
            service = await session.get(Service, order.service_id) if order else None
            user = await session.get(User, record.user_id)
            session.add(Payment(order_id=record.order_id, amount_toman=record.amount_toman,
                                receipt_file_id=None, receipt_type="rialit", status="approved"))
            record.status, record.paid_at = "paid", now
            await session.commit()
            return 200, {"ok": True, "action": "paid_order", "order_id": record.order_id,
                         "public_id": order.public_id if order else "—",
                         "service_name": service.name if service else "خدمت",
                         "user_telegram_id": user.telegram_id if user else None,
                         "amount_toman": record.amount_toman}
        claim = await session.execute(update(WalletTopup).where(
            WalletTopup.id == record.topup_id,
            WalletTopup.status.in_(["awaiting_receipt", "waiting_receipt_review"])
        ).values(status="approved", reviewed_at=now))
        if claim.rowcount != 1:
            record.status = "ignored"
            await session.commit()
            return 200, {"ok": True, "action": "already_paid"}
        topup = await session.get(WalletTopup, record.topup_id)
        wallet = (await session.execute(
            select(Wallet).where(Wallet.user_id == topup.user_id)
        )).scalar_one_or_none()
        if wallet is None:
            wallet = Wallet(user_id=topup.user_id, balance_toman=0)
            session.add(wallet)
            await session.flush()
        await session.execute(update(Wallet).where(Wallet.user_id == topup.user_id)
                              .values(balance_toman=Wallet.balance_toman + record.amount_toman))
        await session.refresh(wallet)
        user = await session.get(User, topup.user_id)
        record.status, record.paid_at = "paid", now
        session.add(WalletTransaction(user_id=topup.user_id, amount_toman=record.amount_toman,
            balance_after_toman=wallet.balance_toman, kind="topup",
            description=f"افزایش اعتبار ریالیت #{topup.id}", topup_id=topup.id))
        await session.commit()
        return 200, {"ok": True, "action": "paid_topup",
                     "user_telegram_id": user.telegram_id if user else None,
                     "amount_toman": record.amount_toman,
                     "new_balance_toman": wallet.balance_toman}
