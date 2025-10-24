### FILE: handlers/quiz_handler.py
"""Handlers for quiz flows."""
from __future__ import annotations

from urllib.parse import unquote_plus

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from keyboards import quiz_options_keyboard
from services import quiz_service
from services.quiz_service import QuizUnavailableError

router = Router()


def _question_with_progress(question: dict, correct_count: int) -> tuple[str, list[str]]:
    """Return formatted question text and options."""
    text = f"{question['question_text']}\n\nTo'g'ri javoblar: {correct_count}/{question['total']}"
    return text, question["options"]


def _handle_quiz_start(user_id: int) -> dict:
    """Start quiz and return question payload."""
    result = quiz_service.start_quiz(user_id)
    return result["question"]


@router.message(Command("quiz"))
async def cmd_quiz(message: Message) -> None:
    """Handle /quiz command."""
    user = message.from_user
    if not user:
        return

    try:
        question = _handle_quiz_start(user.id)
    except QuizUnavailableError:
        await message.answer("Avval /today bosing 😊")
        return

    text, options = _question_with_progress(question, correct_count=0)
    await message.answer(text, reply_markup=quiz_options_keyboard(options))


@router.callback_query(F.data == "quiz_start")
async def cb_quiz_start(callback: CallbackQuery) -> None:
    """Start quiz from inline button."""
    user = callback.from_user
    if not user:
        await callback.answer()
        return

    try:
        question = _handle_quiz_start(user.id)
    except QuizUnavailableError:
        await callback.answer("Avval /today bosing 😊", show_alert=True)
        return

    text, options = _question_with_progress(question, correct_count=0)
    await callback.message.answer(text, reply_markup=quiz_options_keyboard(options))
    await callback.answer()


@router.callback_query(F.data.startswith("quiz_ans|"))
async def cb_quiz_answer(callback: CallbackQuery) -> None:
    """Process a quiz answer option."""
    user = callback.from_user
    if not user or not callback.data:
        await callback.answer()
        return

    encoded = callback.data.split("|", maxsplit=1)[1]
    answer_text = unquote_plus(encoded)

    try:
        result = quiz_service.get_next_question(user.id, answer_text)
    except QuizUnavailableError:
        await callback.answer("Quizni qayta /quiz orqali boshlang.", show_alert=True)
        return

    if result["is_correct"]:
        await callback.answer("Zo'r! ✅")
    else:
        await callback.answer(f"To'g'ri javob: {result['correct_answer']}", show_alert=True)

    if result["status"] == "finished":
        summary = (
            "Zo'r ish! 🎉\n"
            f"To'g'ri javoblar: {result['correct_count']}/{result['total']}\n"
            f"Yangi XP: {result['xp']}\n"
            "Davom etamizmi? /today"
        )
        await callback.message.edit_text(summary)
        return

    question = result["question"]
    text, options = _question_with_progress(question, result["correct_count"])
    await callback.message.edit_text(text, reply_markup=quiz_options_keyboard(options))
