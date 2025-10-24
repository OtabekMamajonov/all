### FILE: config.py
"""Configuration loader for SozMaster AI bot."""
from __future__ import annotations

import os
from typing import List

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

_admin_ids_raw = os.getenv("ADMIN_USER_IDS", "")
ADMIN_IDS: List[int] = []
if _admin_ids_raw:
    ADMIN_IDS = [int(item.strip()) for item in _admin_ids_raw.split(",") if item.strip()]

DB_PATH = os.getenv("DB_PATH", "bot.db")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Tashkent")
