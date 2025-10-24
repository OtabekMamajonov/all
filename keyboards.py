### FILE: keyboards.py
"""Inline keyboard builders for SozMaster AI."""
from __future__ import annotations

from urllib.parse import quote_plus

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def today_actions_keyboard() -> InlineKeyboardMarkup:
    """Return keyboard with shortcuts after /today."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Quizni boshlash", callback_data="quiz_start")
    builder.button(text="📈 Statistika", callback_data="show_stats")
    builder.button(text="⭐ Premiumga o'tish", callback_data="show_upgrade")
    builder.adjust(1)
    return builder.as_markup()


def quiz_options_keyboard(options: list[str]) -> InlineKeyboardMarkup:
    """Build keyboard for quiz answers."""
    builder = InlineKeyboardBuilder()
    for option in options:
        encoded = quote_plus(option)
        builder.button(text=option, callback_data=f"quiz_ans|{encoded}")
    builder.adjust(2)
    return builder.as_markup()
