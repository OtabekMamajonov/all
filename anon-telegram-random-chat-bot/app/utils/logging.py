from __future__ import annotations

import logging
from typing import Optional


def configure_logging(level: str = "INFO") -> None:
    """Configure application-wide logging."""

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a module logger."""

    return logging.getLogger(name if name else "anon_chat")
