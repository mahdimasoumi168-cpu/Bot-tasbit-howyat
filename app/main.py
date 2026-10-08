import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.bot.admin import router as admin_router
from app.bot.handlers import router
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
    dp = Dispatcher()
    dp.include_router(router)
    dp.include_router(admin_router)

    logging.getLogger(__name__).info("Bot is starting")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
