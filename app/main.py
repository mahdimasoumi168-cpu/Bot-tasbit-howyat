import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.bot.handlers import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import init_db


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN در فایل .env تنظیم نشده است.")

    await init_db()

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(router)

    logging.getLogger(__name__).info("Bot is starting")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
