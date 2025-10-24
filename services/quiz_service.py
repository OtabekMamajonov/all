### FILE: services/quiz_service.py
"""Quiz management logic for SozMaster AI."""
from __future__ import annotations

from typing import Any, Dict

import db
from services.word_service import build_quiz_options_for_word
from utils.time import get_tashkent_date_str
from wordbank import WORD_BANK


class QuizUnavailableError(Exception):
    """Raised when a quiz cannot be started or continued."""


def _build_question_payload(words: list[dict], index: int) -> Dict[str, Any]:
    """Prepare question data for the given word index."""
    word_obj = words[index]
    options = build_quiz_options_for_word(word_obj, WORD_BANK)
    total = len(words)
    question_text = (
        f"Savol {index + 1}/{total}\n"
        f"\"{word_obj['word']}\" so'zining ma'nosi qaysi?"
    )
    return {
        "question_text": question_text,
        "options": options,
        "correct_answer": word_obj["translation_uz"],
        "word": word_obj["word"],
        "current_index": index,
        "total": total,
    }


def start_quiz(user_id: int) -> Dict[str, Any]:
    """Initialize quiz for the user and return the first question payload."""
    today = get_tashkent_date_str()
    words = db.get_today_words(user_id, today)
    if not words:
        raise QuizUnavailableError("no words for today")

    total = len(words)
    if total == 0:
        raise QuizUnavailableError("empty word list")

    db.save_quiz_state(user_id, today, 0, 0, total)
    question = _build_question_payload(words, 0)
    return {"status": "question", "question": question}


def get_next_question(user_id: int, selected_option: str) -> Dict[str, Any]:
    """Process user's answer and provide next question or final summary."""
    today = get_tashkent_date_str()
    state = db.get_quiz_state(user_id, today)
    if not state:
        raise QuizUnavailableError("quiz not started")

    words = db.get_today_words(user_id, today)
    if not words:
        db.clear_quiz_state(user_id, today)
        raise QuizUnavailableError("no words for today")

    current_index = state["current_question_index"]
    total = state["total_count"] or len(words)
    if current_index >= total:
        db.clear_quiz_state(user_id, today)
        raise QuizUnavailableError("quiz already completed")

    current_word = words[current_index]
    correct_answer = current_word["translation_uz"]
    is_correct = selected_option == correct_answer

    correct_count = state["correct_count"] or 0
    if is_correct:
        correct_count += 1
        db.add_xp(user_id, 1)

    next_index = current_index + 1

    if next_index >= total:
        db.clear_quiz_state(user_id, today)
        user_row = db.get_user(user_id)
        xp_total = user_row["xp"] if user_row else correct_count
        return {
            "status": "finished",
            "is_correct": is_correct,
            "correct_answer": correct_answer,
            "correct_count": correct_count,
            "total": total,
            "xp": xp_total,
        }

    db.update_quiz_state_on_answer(user_id, today, next_index, correct_count)
    next_question = _build_question_payload(words, next_index)
    return {
        "status": "next",
        "is_correct": is_correct,
        "correct_answer": correct_answer,
        "correct_count": correct_count,
        "total": total,
        "question": next_question,
    }
