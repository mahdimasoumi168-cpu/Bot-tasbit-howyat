import asyncio
import json
import logging
import os
from pathlib import Path

from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import SimpleEventIsolation

from app.bot.admin import router as admin_router
from app.bot.handlers import router
from app.bot.vpn import router as vpn_router
from app.bot.sqlite_fsm import SQLiteFSMStorage
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.seed import seed_services
from app.db.session import init_db
from app.payments.variza import process_webhook
from app.payments.rialit import process_rialit_webhook


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN در متغیر محیطی BOT_TOKEN تنظیم نشده است.")

    await init_db()
    await seed_services()

    bot = Bot(token=settings.bot_token)

    if settings.database_url.startswith("sqlite"):
        raw_db_path = settings.database_url.split(":///", 1)[-1]
        db_path = Path(raw_db_path)
        fsm_path = db_path.with_name("fsm.db")
        persistent_root = Path("/data").resolve()
        resolved_db_path = db_path.resolve()
        try:
            resolved_db_path.relative_to(persistent_root)
        except ValueError:
            logging.getLogger(__name__).warning(
                "SQLite DATABASE_URL points outside Railway's /data persistent volume; "
                "existing database path was preserved to avoid silently switching databases."
            )
    else:
        # Form progress must survive restarts even when the business database is PostgreSQL.
        fsm_path = Path("/data/fsm.db")

    storage = SQLiteFSMStorage(str(fsm_path))
    dp = Dispatcher(storage=storage, events_isolation=SimpleEventIsolation())
    dp.include_router(router)
    dp.include_router(vpn_router)
    dp.include_router(admin_router)

    async def health(_request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    app = web.Application()
    app.router.add_get("/health", health)

    async def variza_webhook(request: web.Request) -> web.Response:
        raw_body = await request.read()
        signature = request.headers.get("X-Webhook-Signature", "")
        status_code, result = await process_webhook(raw_body, signature)
        if status_code == 200:
            action = result.get("action")
            try:
                if action == "paid_order":
                    user_id = result.get("user_telegram_id")
                    if user_id:
                        await bot.send_message(
                            user_id,
                            f"✅ پرداخت واریزا تأیید شد.\n"
                            f"🔢 شماره درخواست: {result.get('public_id', '—')}\n"
                            f"📌 خدمت: {result.get('service_name', 'خدمت')}\n"
                            f"💰 مبلغ: {int(result.get('amount_toman', 0)):,} تومان\n\n"
                            "پرونده برای بررسی و انجام خدمت در صف قرار گرفت.",
                        )
                    try:
                        from app.bot.admin import send_case_to_operator
                        await send_case_to_operator(bot, int(result["order_id"]))
                    except Exception:
                        logging.getLogger(__name__).exception(
                            "Variza payment succeeded but operator notification failed"
                        )
                elif action == "paid_vpn":
                    user_id = result.get("user_telegram_id")
                    months = result.get("months") or "—"
                    gigabytes = result.get("gigabytes") or "—"
                    if user_id:
                        await bot.send_message(
                            user_id,
                            "✅ پرداخت VPN با ریالیت تأیید شد.\n"
                            f"⏳ مدت انتخابی: {months} ماه\n"
                            f"📦 حجم: {gigabytes} گیگابایت\n"
                            f"💰 مبلغ: {int(result.get('amount_toman', 0)):,} تومان\n\n"
                            "⚠️ پرداخت ثبت شده است؛ فعال‌سازی خودکار VPN در این نسخه انجام نمی‌شود."
                        )
                    for admin_id in get_settings().admin_id_set:
                        try:
                            await bot.send_message(
                                admin_id,
                                "🔔 پرداخت VPN تأیید شد و برای فعال‌سازی دستی نیاز به بررسی دارد.\n"
                                f"شناسه تلگرام: {user_id or '—'}\n"
                                f"مدت: {months} ماه | حجم: {gigabytes} گیگابایت\n"
                                f"مبلغ: {int(result.get('amount_toman', 0)):,} تومان"
                            )
                        except Exception:
                            pass
                elif action == "paid_topup":
                    user_id = result.get("user_telegram_id")
                    if user_id:
                        await bot.send_message(
                            user_id,
                            f"✅ افزایش اعتبار با واریزا تأیید شد.\n"
                            f"💰 مبلغ: {int(result.get('amount_toman', 0)):,} تومان\n"
                            f"💳 موجودی جدید: {int(result.get('new_balance_toman', 0)):,} تومان",
                        )
                elif action == "paid_vpn":
                    user_id = result.get("user_telegram_id")
                    if user_id:
                        await bot.send_message(
                            user_id,
                            "✅ پرداخت VPN با ریالیت از سمت درگاه تأیید شد.\n"
                            f"⏳ مدت انتخابی: {int(result.get('months') or 0)} ماه\n"
                            f"📦 حجم: {int(result.get('gigabytes') or 0)} گیگابایت\n"
                            f"💰 مبلغ: {int(result.get('amount_toman') or 0):,} تومان\n\n"
                            "توجه: تأیید پرداخت ثبت شد؛ فعال‌سازی خودکار اشتراک VPN هنوز به سامانه تأمین‌کننده متصل نیست.",
                        )
                elif action == "already_paid":
                    for admin_id in get_settings().admin_id_set:
                        try:
                            await bot.send_message(
                                admin_id,
                                "⚠️ واریزا یک پرداخت موفق دیگر برای پرونده/شارژ ثبت‌شده ارسال کرد، "
                                "اما مورد قبلاً پرداخت شده بود. لطفاً تراکنش را در پنل واریزا بررسی کنید.\n"
                                f"جزئیات: {json.dumps(result, ensure_ascii=False)}",
                            )
                        except Exception:
                            pass
            except Exception:
                logging.getLogger(__name__).exception(
                    "Variza webhook processed but user notification failed"
                )
        return web.json_response(result, status=status_code)

    async def variza_return(_request: web.Request) -> web.Response:
        return web.Response(
            text=(
                "<!doctype html><html lang='fa' dir='rtl'><meta charset='utf-8'>"
                "<meta name='viewport' content='width=device-width,initial-scale=1'>"
                "<title>بازگشت از واریزا</title>"
                "<body style='font-family:sans-serif;max-width:640px;margin:48px auto;padding:16px'>"
                "<h2>بازگشت از درگاه واریزا</h2>"
                "<p>اگر پرداخت را انجام داده‌اید، نتیجه پس از تأیید واریزا به ربات ارسال می‌شود.</p>"
                "<p>برای جلوگیری از پرداخت تکراری، تا دریافت پیام تأیید ربات صبر کنید.</p>"
                "</body></html>"
            ),
            content_type="text/html",
            charset="utf-8",
        )

    async def rialit_webhook(request: web.Request) -> web.Response:
        # Rialit may return to callback_url with a token query parameter.
        # Accept query parameters and JSON bodies; server-side verification
        # in process_rialit_webhook remains the only payment confirmation.
        payload = dict(request.query)
        if request.can_read_body:
            try:
                body = await request.json()
                if isinstance(body, dict):
                    payload.update(body)
            except (json.JSONDecodeError, ValueError):
                if not payload:
                    return web.json_response({"ok": False, "error": "invalid_json"}, status=400)
        if not payload:
            return web.json_response({"ok": False, "error": "missing_token"}, status=400)
        status_code, result = await process_rialit_webhook(payload)
        if status_code == 200:
            action = result.get("action")
            try:
                if action == "paid_order":
                    user_id = result.get("user_telegram_id")
                    if user_id:
                        await bot.send_message(
                            user_id,
                            f"✅ پرداخت ریالیت تأیید شد.\\n"
                            f"🔢 شماره درخواست: {result.get('public_id', '—')}\\n"
                            f"📌 خدمت: {result.get('service_name', 'خدمت')}\\n"
                            f"💰 مبلغ: {int(result.get('amount_toman', 0)):,} تومان\\n\\n"
                            "پرونده برای بررسی و انجام خدمت در صف قرار گرفت.",
                        )
                    try:
                        from app.bot.admin import send_case_to_operator
                        await send_case_to_operator(bot, int(result["order_id"]))
                    except Exception:
                        logging.getLogger(__name__).exception(
                            "Rialit payment succeeded but operator notification failed"
                        )
                elif action == "paid_topup":
                    user_id = result.get("user_telegram_id")
                    if user_id:
                        await bot.send_message(
                            user_id,
                            f"✅ افزایش اعتبار با ریالیت تأیید شد.\\n"
                            f"💰 مبلغ: {int(result.get('amount_toman', 0)):,} تومان\\n"
                            f"💳 موجودی جدید: {int(result.get('new_balance_toman', 0)):,} تومان",
                        )
                elif action == "already_paid":
                    for admin_id in get_settings().admin_id_set:
                        try:
                            await bot.send_message(
                                admin_id,
                                "⚠️ ریالیت پرداختی برای پرونده/شارژ ثبت کرد که قبلاً پرداخت شده بود؛ لطفاً تراکنش را بررسی کنید.\\n"
                                f"جزئیات: {json.dumps(result, ensure_ascii=False)}",
                            )
                        except Exception:
                            pass
            except Exception:
                logging.getLogger(__name__).exception(
                    "Rialit webhook processed but notification failed"
                )
        return web.json_response(result, status=status_code)

    app.router.add_post("/webhooks/variza", variza_webhook)
    app.router.add_post("/webhooks/rialit", rialit_webhook)
    app.router.add_get("/webhooks/rialit", rialit_webhook)
    app.router.add_get("/payments/variza/return", variza_return)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", "8080")))
    await site.start()

    logging.getLogger(__name__).info("Bot polling and HTTP webhook server are starting")
    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()
        await storage.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
