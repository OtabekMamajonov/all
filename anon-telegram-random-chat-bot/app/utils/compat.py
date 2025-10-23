from __future__ import annotations

from typing import Any, Callable

try:  # pragma: no cover - real aiogram in production
    from aiogram import Bot, Dispatcher, Router
    from aiogram.client.default import DefaultBotProperties
    from aiogram.exceptions import TelegramAPIError
    from aiogram.filters import Command, CommandStart
    from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
except ModuleNotFoundError:  # pragma: no cover - lightweight stubs for tests
    class Router:  # type: ignore[override]
        def message(self, *args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            def decorator(handler: Callable[..., Any]) -> Callable[..., Any]:
                return handler

            return decorator

    class Bot:  # type: ignore[override]
        pass

    class Dispatcher:  # type: ignore[override]
        def include_router(self, router: Router) -> None:
            pass

        async def start_polling(self, bot: Bot) -> None:
            raise RuntimeError("Dispatcher is unavailable without aiogram installed")

        def __setitem__(self, key: str, value: Any) -> None:
            pass

        @property
        def workflow_data(self) -> dict[str, Any]:
            return {}

    class DefaultBotProperties:  # type: ignore[override]
        def __init__(self, **_: Any) -> None:
            pass

    class Command:  # type: ignore[override]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    class CommandStart(Command):  # type: ignore[override]
        pass

    class Message:  # type: ignore[override]
        from_user: Any

        async def answer(self, *_: Any, **__: Any) -> None:  # pragma: no cover - stub
            raise RuntimeError("Message.answer is not implemented in stub")

    class KeyboardButton:  # type: ignore[override]
        def __init__(self, text: str) -> None:
            self.text = text

    class ReplyKeyboardMarkup:  # type: ignore[override]
        def __init__(self, **_: Any) -> None:
            pass

    class TelegramAPIError(Exception):
        pass

__all__ = [
    "Bot",
    "Dispatcher",
    "Router",
    "DefaultBotProperties",
    "TelegramAPIError",
    "Command",
    "CommandStart",
    "KeyboardButton",
    "Message",
    "ReplyKeyboardMarkup",
]
