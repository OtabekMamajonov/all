### FILE: handlers/upgrade_handler.py
"""Handlers that explain premium benefits."""
from __future__ import annotations

from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

import db
from utils.time import is_premium

router = Router()


def _upgrade_text(user_row) -> str:
    """Return descriptive upgrade message."""
    base = (
        "Premium rejimda:\n"
        "• Har kuni 20 ta yangi so'z\n"
        "• Audio talaffuz (tez orada)\n"
        "• Haftalik hisobot\n"
        "• Cheksiz /quiz va /more\n\n"
        "Hozircha to'lov qo'lda tasdiqlanadi.\n"
        "Admin bilan bog'laning yoki promokod oling."
    )

    if user_row and is_premium(user_row):
        try:
            expires = datetime.fromisoformat(user_row["premium_until"])
            expiry_text = expires.strftime("%Y-%m-%d")
        except Exception:  # pragma: no cover - defensive
            expiry_text = "noma'lum"
        status = f"\n\nSiz allaqachon Premiumsiz! ⭐ Amal qilish muddati: {expiry_text}"
    else:
        status = "\n\nPremiumga o'tish uchun /make_premium orqali admin bilan bog'laning."

    return base + status


@router.message(Command("upgrade"))
async def cmd_upgrade(message: Message) -> None:
    """Describe premium plan."""
    user = message.from_user
    if not user:
        return

    user_row = db.get_user(user.id)
    await message.answer(_upgrade_text(user_row))


@router.callback_query(lambda c: c.data == "show_upgrade")
async def cb_show_upgrade(callback: CallbackQuery) -> None:
    """Handle inline button for upgrade info."""
    user = callback.from_user
    if not user:
        await callback.answer()
        return

    user_row = db.get_user(user.id)
    await callback.message.answer(_upgrade_text(user_row))
    await callback.answer()
