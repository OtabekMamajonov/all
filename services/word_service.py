### FILE: services/word_service.py
"""Word management services for SozMaster AI."""
from __future__ import annotations

import random
from typing import List, Tuple

import db
from utils.time import get_tashkent_date_str, is_premium
from wordbank import WORD_BANK


def _collect_words(start_index: int, count: int) -> Tuple[list[dict], int]:
    """Collect a sequential slice of words from the bank with wrap-around."""
    total_words = len(WORD_BANK)
    selected: List[dict] = []
    index = start_index
    for _ in range(count):
        word = WORD_BANK[index % total_words]
        selected.append(dict(word))
        index += 1
    return selected, index % total_words


def get_or_assign_today_words(user_id: int, username: str | None) -> list[dict]:
    """Return today's words for the user, assigning them if needed."""
    today = get_tashkent_date_str()
    existing = db.get_today_words(user_id, today)
    if existing:
        return existing

    user = db.get_or_create_user(user_id, username)
    word_count = 20 if is_premium(user) else 5
    start_index = user["last_word_index"] or 0
    selected, new_index = _collect_words(start_index, word_count)

    from db import calculate_new_streak  # Local import to avoid circularity

    previous_streak = user["streak"] or 0
    new_streak = calculate_new_streak(user.get("last_active_date"), today, previous_streak)

    db.save_today_words(user_id, today, selected)
    db.update_user_after_today_request(user_id, new_index, new_streak, today)
    return selected


def assign_additional_words(user_id: int, username: str | None, count: int = 5) -> list[dict]:
    """Assign additional practice words for premium users."""
    user = db.get_or_create_user(user_id, username)
    start_index = user["last_word_index"] or 0
    selected, new_index = _collect_words(start_index, count)

    from db import calculate_new_streak

    today = get_tashkent_date_str()
    previous_streak = user["streak"] or 0
    new_streak = calculate_new_streak(user.get("last_active_date"), today, previous_streak)
    db.update_user_after_today_request(user_id, new_index, new_streak, today)
    return selected


def format_words_for_user(words_list: list[dict]) -> str:
    """Format word list into a friendly Uzbek message."""
    lines = ["Bugungi so'zlaring 🔥", ""]
    for idx, word in enumerate(words_list, start=1):
        lines.append(f"{idx}) {word['word']}")
        lines.append(f"   talaffuz: {word['pronunciation']}")
        lines.append(f"   ma'nosi: {word['translation_uz']}")
        lines.append(f"   misol: {word['example']}")
        lines.append(f"   mashq: {word['exercise']}")
        lines.append("")

    lines.append("Quiz qilish uchun: /quiz")
    lines.append("Statistika: /stats")
    lines.append("Premium: /upgrade")
    return "\n".join(lines)


def build_quiz_options_for_word(target_word: dict, all_words_list: list[dict] | None = None) -> list[str]:
    """Generate multiple-choice options for a quiz question."""
    if all_words_list is None:
        all_words_list = WORD_BANK

    correct = target_word["translation_uz"]
    pool = [w["translation_uz"] for w in all_words_list if w["translation_uz"] != correct]
    wrong_choices = random.sample(pool, k=3)
    options = wrong_choices + [correct]
    random.shuffle(options)
    return options
