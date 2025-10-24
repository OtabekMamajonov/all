### FILE: handlers/today_handler.py
"""Handlers related to daily words delivery."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

import db
from keyboards import today_actions_keyboard
from services import word_service
from utils.time import get_tashkent_date_str, is_premium

router = Router()


@router.message(Command("today"))
async def cmd_today(message: Message) -> None:
    """Send today's words to the user."""
    user = message.from_user
    if not user:
        return

    username = user.username or user.full_name
    words = word_service.get_or_assign_today_words(user.id, username)
    formatted = word_service.format_words_for_user(words)
    await message.answer(formatted, reply_markup=today_actions_keyboard())


@router.message(Command("more"))
async def cmd_more(message: Message) -> None:
    """Provide extra words for premium users."""
    user = message.from_user
    if not user:
        return

    user_row = db.get_user(user.id)
    if not is_premium(user_row):
        await message.answer(
            "Bu funksiya faqat Premium uchun ⭐\n"
            "Premium foydali tomoni:\n"
            "• kuniga 20 ta so'z\n"
            "• bonus mashqlar\n"
            "• ovozli talaffuz\n"
            "/upgrade orqali batafsil"
        )
        return

    username = user.username or user.full_name
    today = get_tashkent_date_str()
    if not db.get_today_words(user.id, today):
        word_service.get_or_assign_today_words(user.id, username)

    extra_words = word_service.assign_additional_words(user.id, username, count=5)
    extra_message = word_service.format_words_for_user(extra_words)
    extra_message = extra_message.replace("Bugungi so'zlaring 🔥", "Bonus so'zlar ⭐", 1)
    await message.answer(extra_message)
