from __future__ import annotations

from .utils.compat import KeyboardButton, ReplyKeyboardMarkup


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/find"), KeyboardButton(text="/next")],
            [KeyboardButton(text="/end"), KeyboardButton(text="/block")],
            [KeyboardButton(text="/report"), KeyboardButton(text="/video")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Type your anonymous message…",
    )
