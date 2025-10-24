from __future__ import annotations

import json
from importlib import resources
from typing import Dict

_MESSAGES: Dict[str, str] = {}


def load_messages(locale: str = "en") -> None:
    global _MESSAGES
    package = __package__ or "app.i18n"
    filename = f"{locale}.json"
    with resources.files(package).joinpath(filename).open("r", encoding="utf-8") as fh:
        _MESSAGES = json.load(fh)


def gettext(key: str, **params: str) -> str:
    if not _MESSAGES:
        load_messages()
    template = _MESSAGES.get(key, key)
    if params:
        return template.format(**params)
    return template


__all__ = ["gettext", "load_messages"]
