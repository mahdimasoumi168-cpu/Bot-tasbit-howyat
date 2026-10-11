import asyncio
import logging
import os
from pathlib import Path

from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import SimpleEventIsolation

from app.bot.admin import router as admin_router
from app.bot.handlers import router
from app.bot.sqlite_fsm import SQLiteFSMStorage
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.seed import seed_services
from app.db.session import init_db


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
    dp.include_router(admin_router)

    async def health(_request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    app = web.Application()
    app.router.add_get("/health", health)
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
