### FILE: handlers/admin_handler.py
"""Administrative handlers."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

import db

router = Router()


@router.message(Command("make_premium"))
async def cmd_make_premium(message: Message) -> None:
    """Grant premium access to a user if caller is admin."""
    user = message.from_user
    if not user:
        return

    if not db.is_user_admin(user.id):
        await message.answer("Bu buyruq faqat adminlar uchun.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Foydalanish: /make_premium <user_id> [kunlar]")
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer("User ID faqat raqamlardan iborat bo'lishi kerak.")
        return

    days = 30
    if len(parts) >= 3:
        try:
            days = int(parts[2])
        except ValueError:
            await message.answer("Kunlar qiymati noto'g'ri.")
            return

    db.get_or_create_user(target_id, None)
    db.mark_user_premium(target_id, days=days)
    await message.answer(f"Foydalanuvchi {target_id} {days} kunga Premiumga o'tkazildi.")
