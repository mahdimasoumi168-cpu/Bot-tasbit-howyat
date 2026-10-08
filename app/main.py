import asyncio
import logging
from pathlib import Path

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
        db_path = Path(raw_db_path if raw_db_path.startswith("/") else "/" + raw_db_path)
        fsm_path = db_path.with_name("fsm.db")
    else:
        fsm_path = Path("data/fsm.db")

    storage = SQLiteFSMStorage(str(fsm_path))
    dp = Dispatcher(storage=storage, events_isolation=SimpleEventIsolation())
    dp.include_router(router)
    dp.include_router(admin_router)

    logging.getLogger(__name__).info("Bot is starting")
    try:
        await dp.start_polling(bot)
    finally:
        await storage.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
