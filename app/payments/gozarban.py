"""Gozarban subscription provisioning API client.

The permanent developer token is stored in GOZARBAN_API_TOKEN. Never log or
return the token to a user. Subscription creation is made idempotent by using
a stable username derived from the paid Rialit payment ID and checking for an
existing subscription before creating one.
"""
from __future__ import annotations

import json
import logging
from typing import Any
import aiohttp

from app.core.config import get_settings

logger = logging.getLogger(__name__)
DEFAULT_API_ROOT = "https://gozarban.com"


class GozarbanError(RuntimeError):
    """Safe error for the Gozarban provisioning integration."""


def _config() -> tuple[str, int, str]:
    settings = get_settings()
    token = settings.gozarban_api_token.strip()
    plan_id = settings.gozarban_plan_id
    root = settings.gozarban_api_root.strip().rstrip("/")
    if not token:
        raise GozarbanError("اتصال گذربان تنظیم نشده است.")
    if not plan_id or plan_id < 1:
        raise GozarbanError("شناسه پلن گذربان تنظیم نشده است.")
    if not root.startswith("https://"):
        raise GozarbanError("نشانی API گذربان معتبر نیست.")
    return token, plan_id, root


def vpn_username(payment_id: int, telegram_user_id: int) -> str:
    """Stable provider username to avoid duplicate subscriptions on webhook retries."""
    return f"nyvpn{telegram_user_id}_{payment_id}"


def _subscription_link(payload: dict[str, Any]) -> str | None:
    external = payload.get("external_data")
    if isinstance(external, dict):
        link = external.get("subscription_url")
        if isinstance(link, str) and link.startswith("https://"):
            return link
        links = external.get("links")
        if isinstance(links, list):
            valid = [item for item in links if isinstance(item, str) and item.startswith(("https://", "vless://", "vmess://", "trojan://", "ss://"))]
            if valid:
                return "\n".join(valid)
    for key in ("subscription_url", "subscription_link", "url"):
        link = payload.get(key)
        if isinstance(link, str) and link.startswith(("https://", "vless://", "vmess://", "trojan://", "ss://")):
            return link
    return None


async def ensure_vpn_subscription(
    *,
    payment_id: int,
    telegram_user_id: int,
    gigabytes: int,
    months: int,
) -> dict[str, Any]:
    """Find or create a paid VPN subscription. Safe to retry for the same payment."""
    if payment_id < 1 or telegram_user_id < 1:
        raise GozarbanError("شناسه پرداخت یا مشترک معتبر نیست.")
    if gigabytes not in range(10, 101, 10) or months not in (1, 2, 3, 4):
        raise GozarbanError("حجم یا مدت اشتراک VPN معتبر نیست.")

    token, plan_id, root = _config()
    username = vpn_username(payment_id, telegram_user_id)
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(timeout=timeout) as client:
        # If a previous request created the subscription but the response was
        # lost, locate the deterministic username before attempting creation.
        async with client.get(
            f"{root}/api/user/subscriptions",
            params={"search": username, "skip": 0, "limit": 10},
            headers=headers,
        ) as response:
            raw = await response.text()
            try:
                result = json.loads(raw)
            except ValueError:
                result = {}
            if response.status == 200 and isinstance(result, dict):
                entries = result.get("subscriptions", [])
                if isinstance(entries, list):
                    for entry in entries:
                        if not isinstance(entry, dict):
                            continue
                        if entry.get("marzban_username") == username or entry.get("display_name") == username:
                            return {
                                "username": username,
                                "subscription_id": entry.get("id"),
                                "subscription_url": _subscription_link(entry),
                                "already_existed": True,
                            }
            elif response.status not in (200, 404):
                logger.warning("Gozarban subscription lookup returned HTTP %s", response.status)
                raise GozarbanError("بررسی اشتراک در گذربان ناموفق بود؛ دوباره تلاش می‌شود.")

        body = {
            "data_size_gb": str(gigabytes),
            "expire_days": str(months * 30),
            "plan_id": plan_id,
            "username": username,
        }
        async with client.post(
            f"{root}/api/user/subscription/create",
            json=body,
            headers={**headers, "Content-Type": "application/json"},
        ) as response:
            raw = await response.text()
            try:
                result = __import__("json").loads(raw)
            except ValueError:
                result = {}
            if response.status not in (200, 201) or not isinstance(result, dict):
                # Never include raw API response: it may contain sensitive data.
                logger.warning("Gozarban subscription create returned HTTP %s", response.status)
                raise GozarbanError("ساخت اشتراک در گذربان انجام نشد؛ موجودی پنل و تنظیمات API را بررسی کنید.")
            return {
                "username": username,
                "subscription_id": result.get("id"),
                "subscription_url": _subscription_link(result),
                "already_existed": False,
            }
