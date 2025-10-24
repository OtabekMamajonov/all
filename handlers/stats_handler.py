### FILE: handlers/stats_handler.py
"""Handlers showing user statistics."""
from __future__ import annotations

from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

import db
from utils.time import is_premium

router = Router()


def _stats_text(user_row) -> str:
    """Build a user-friendly statistics message."""
    if not user_row:
        return "Ma'lumot topilmadi. Avval /start buyrug'ini yuboring."

    xp = user_row["xp"] or 0
    streak = user_row["streak"] or 0

    if is_premium(user_row):
        try:
            expires = datetime.fromisoformat(user_row["premium_until"])
            if expires.tzinfo is None:
                expiry_text = expires.strftime("%Y-%m-%d")
            else:
                expiry_text = expires.date().isoformat()
        except Exception:  # pragma: no cover - defensive
            expiry_text = "noma'lum"
        premium_line = f"Premium holati: ⭐ {expiry_text} gacha"
    else:
        premium_line = "Premium holati: Oddiy foydalanuvchi"

    return (
        "Statistikang 📈\n\n"
        f"XP: {xp}\n"
        f"Ketma-ket kunlar: {streak}\n"
        f"{premium_line}"
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Handle /stats command."""
    user = message.from_user
    if not user:
        return

    user_row = db.get_user(user.id) or db.get_or_create_user(user.id, user.username or user.full_name)
    await message.answer(_stats_text(user_row))


@router.callback_query(lambda c: c.data == "show_stats")
async def cb_show_stats(callback: CallbackQuery) -> None:
    """Handle inline stats button."""
    user = callback.from_user
    if not user:
        await callback.answer()
        return

    user_row = db.get_user(user.id) or db.get_or_create_user(user.id, user.username or user.full_name)
    await callback.message.answer(_stats_text(user_row))
    await callback.answer()
