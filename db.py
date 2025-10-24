### FILE: db.py
"""Database helper utilities for SozMaster AI."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import Iterable

from config import ADMIN_IDS, DB_PATH
from utils.time import get_yesterday_date_str


@contextmanager
def get_connection() -> Iterable[sqlite3.Connection]:
    """Yield an SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Initialize database tables if they do not exist."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                is_premium INTEGER DEFAULT 0,
                premium_until TEXT,
                xp INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0,
                last_active_date TEXT,
                last_word_index INTEGER DEFAULT 0
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user_daily_words (
                user_id INTEGER,
                date TEXT,
                words_json TEXT,
                PRIMARY KEY (user_id, date)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS quiz_progress (
                user_id INTEGER,
                date TEXT,
                current_question_index INTEGER,
                correct_count INTEGER,
                total_count INTEGER,
                PRIMARY KEY (user_id, date)
            )
            """
        )
        conn.commit()


def get_or_create_user(user_id: int, username: str | None) -> sqlite3.Row:
    """Fetch existing user or create a new one."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row:
            if username and row["username"] != username:
                cur.execute(
                    "UPDATE users SET username = ? WHERE user_id = ?",
                    (username, user_id),
                )
                conn.commit()
                cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                row = cur.fetchone()
            return row

        cur.execute(
            """
            INSERT INTO users (user_id, username, is_premium, xp, streak, last_word_index)
            VALUES (?, ?, 0, 0, 0, 0)
            """,
            (user_id, username),
        )
        conn.commit()
        cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return cur.fetchone()


def get_user(user_id: int) -> sqlite3.Row | None:
    """Return user row if present."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return cur.fetchone()


def calculate_new_streak(
    old_last_active_date: str | None,
    today_date_str: str,
    previous_streak: int | None = None,
) -> int:
    """Calculate streak based on last active date and today's date."""
    if previous_streak is None:
        previous_streak = 0

    if not old_last_active_date:
        return 1

    if old_last_active_date == today_date_str:
        return max(1, previous_streak)

    if old_last_active_date == get_yesterday_date_str():
        return previous_streak + 1

    return 1


def update_user_after_today_request(
    user_id: int,
    new_last_word_index: int,
    new_streak: int,
    new_last_active_date: str,
) -> None:
    """Update user's progress information after /today command."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE users
            SET last_word_index = ?, streak = ?, last_active_date = ?
            WHERE user_id = ?
            """,
            (new_last_word_index, new_streak, new_last_active_date, user_id),
        )
        conn.commit()


def save_today_words(user_id: int, date_str: str, words_list: list[dict]) -> None:
    """Persist today's assigned words for the user."""
    words_json = json.dumps(words_list, ensure_ascii=False)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO user_daily_words (user_id, date, words_json)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET words_json=excluded.words_json
            """,
            (user_id, date_str, words_json),
        )
        conn.commit()


def get_today_words(user_id: int, date_str: str) -> list[dict] | None:
    """Return today's words for the user if already assigned."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT words_json FROM user_daily_words WHERE user_id = ? AND date = ?",
            (user_id, date_str),
        )
        row = cur.fetchone()
        if not row:
            return None
        return json.loads(row["words_json"])


def save_quiz_state(
    user_id: int,
    date_str: str,
    current_question_index: int,
    correct_count: int,
    total_count: int,
) -> None:
    """Create or replace quiz state for the user."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO quiz_progress (user_id, date, current_question_index, correct_count, total_count)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, date)
            DO UPDATE SET current_question_index=excluded.current_question_index,
                          correct_count=excluded.correct_count,
                          total_count=excluded.total_count
            """,
            (user_id, date_str, current_question_index, correct_count, total_count),
        )
        conn.commit()


def get_quiz_state(user_id: int, date_str: str) -> sqlite3.Row | None:
    """Return stored quiz progress for today."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM quiz_progress WHERE user_id = ? AND date = ?",
            (user_id, date_str),
        )
        return cur.fetchone()


def update_quiz_state_on_answer(
    user_id: int,
    date_str: str,
    current_question_index: int,
    correct_count: int,
) -> None:
    """Update quiz progress after processing an answer."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE quiz_progress
            SET current_question_index = ?, correct_count = ?
            WHERE user_id = ? AND date = ?
            """,
            (current_question_index, correct_count, user_id, date_str),
        )
        conn.commit()


def clear_quiz_state(user_id: int, date_str: str) -> None:
    """Remove quiz state when quiz is completed."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM quiz_progress WHERE user_id = ? AND date = ?",
            (user_id, date_str),
        )
        conn.commit()


def add_xp(user_id: int, amount: int) -> None:
    """Increase user's XP by the given amount."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET xp = COALESCE(xp, 0) + ? WHERE user_id = ?",
            (amount, user_id),
        )
        conn.commit()


def mark_user_premium(user_id: int, days: int = 30) -> None:
    """Mark a user as premium for the given number of days."""
    now = datetime.now(UTC)
    expires_at = now + timedelta(days=days)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE users
            SET is_premium = 1, premium_until = ?
            WHERE user_id = ?
            """,
            (expires_at.isoformat(), user_id),
        )
        conn.commit()


def is_user_admin(user_id: int) -> bool:
    """Return True if the user is in the admin list."""
    return user_id in ADMIN_IDS
