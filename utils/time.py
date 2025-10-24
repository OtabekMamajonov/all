### FILE: utils/time.py
"""Time helpers for SozMaster AI."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from config import TIMEZONE


def get_tashkent_date_str() -> str:
    """Return today's date string in Asia/Tashkent timezone."""
    tz = ZoneInfo(TIMEZONE)
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%d")


def now_utc_iso() -> str:
    """Return current UTC time formatted as ISO string."""
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def is_premium(user_row: dict | None) -> bool:
    """Determine whether a user row represents a premium user."""
    if not user_row:
        return False

    premium_until = user_row.get("premium_until")
    if not premium_until:
        return False

    try:
        premium_dt = datetime.fromisoformat(premium_until)
    except ValueError:
        return False

    return premium_dt > datetime.now(UTC)


def get_yesterday_date_str() -> str:
    """Return yesterday's date string in Asia/Tashkent timezone."""
    tz = ZoneInfo(TIMEZONE)
    now = datetime.now(tz)
    yesterday = now - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")
