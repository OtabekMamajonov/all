### FILE: handlers/start_handler.py
"""Handler for the /start command."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

import db

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Greet the user and register them in the database."""
    user = message.from_user
    if not user:
        return

    username = user.username or user.full_name
    db.get_or_create_user(user.id, username)

    text = (
        "Salom 👋 Bu SozMaster AI.\n"
        "Men har kuni senga yangi inglizcha so'zlarni o'rgataman.\n"
        "Boshlash uchun /today bos.\n\n"
        "Asosiy buyruqlar:\n"
        "• /today – bugungi so'zlar\n"
        "• /quiz – bugungi mini-quiz\n"
        "• /stats – XP va streak\n"
        "• /upgrade – Premium haqida\n"
    )
    await message.answer(text)
