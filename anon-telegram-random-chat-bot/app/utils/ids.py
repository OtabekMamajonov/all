from __future__ import annotations

import hashlib
import secrets
from typing import Optional


def generate_session_id() -> str:
    """Return a secure random session identifier."""

    return secrets.token_urlsafe(16)


def mask_user_id(user_id: int, salt: Optional[str] = None) -> str:
    """Hash a Telegram user id for safe logging/reporting."""

    hasher = hashlib.sha256()
    hasher.update(str(user_id).encode("utf-8"))
    if salt:
        hasher.update(salt.encode("utf-8"))
    return hasher.hexdigest()


def build_jitsi_room(session_id: str) -> str:
    """Return a per-session room fragment for Jitsi meetings."""

    random_tail = secrets.token_urlsafe(6)
    return f"anon-{session_id}-{random_tail}"
