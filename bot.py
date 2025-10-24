### FILE: bot.py
"""Entry point for SozMaster AI Telegram bot."""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

import config
import db
from handlers import (
    admin_handler,
    quiz_handler,
    start_handler,
    stats_handler,
    today_handler,
    upgrade_handler,
)


async def main() -> None:
    """Initialize bot components and start polling."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    db.init_db()

    if not config.BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable must be set.")

    bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    dp.include_router(start_handler.router)
    dp.include_router(today_handler.router)
    dp.include_router(quiz_handler.router)
    dp.include_router(stats_handler.router)
    dp.include_router(upgrade_handler.router)
    dp.include_router(admin_handler.router)

    logging.info("SozMaster AI ishga tushdi.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")
