from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Iterator

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.i18n import load_messages
from app.matching import MatchingService
from app.storage import Storage
from app.utils.ratelimit import RateLimiter


@pytest.fixture(scope="session", autouse=True)
def _load_translations() -> None:
    load_messages("en")


@pytest.fixture()
def storage(tmp_path: Path) -> Iterator[Storage]:
    db_path = tmp_path / "test.sqlite3"
    store = Storage(str(db_path), session_ttl=0)
    asyncio.run(store.init())
    try:
        yield store
    finally:
        asyncio.run(store.close())


@pytest.fixture()
def matching(storage: Storage) -> MatchingService:
    return MatchingService(storage)


@pytest.fixture()
def rate_limiter() -> Iterator[RateLimiter]:
    limiter = asyncio.run(RateLimiter.create(redis_url=None))
    try:
        yield limiter
    finally:
        asyncio.run(limiter.close())


class DummyBot:
    def __init__(self) -> None:
        self.sent: list[tuple[str, int, str]] = []

    async def send_message(self, chat_id: int, text: str) -> None:
        self.sent.append(("message", chat_id, text))

    async def send_voice(self, chat_id: int, voice: str) -> None:
        self.sent.append(("voice", chat_id, voice))

    async def send_photo(self, chat_id: int, photo: str, caption: str | None = None) -> None:
        payload = photo if caption is None else f"{photo}:{caption}"
        self.sent.append(("photo", chat_id, payload))

    async def send_video(self, chat_id: int, video: str, caption: str | None = None) -> None:
        payload = video if caption is None else f"{video}:{caption}"
        self.sent.append(("video", chat_id, payload))

    async def send_document(self, chat_id: int, document: str, caption: str | None = None) -> None:
        payload = document if caption is None else f"{document}:{caption}"
        self.sent.append(("document", chat_id, payload))

    async def send_sticker(self, chat_id: int, sticker: str) -> None:
        self.sent.append(("sticker", chat_id, sticker))


class DummyMessage:
    def __init__(self, user_id: int, text: str | None = None) -> None:
        self.from_user = SimpleNamespace(id=user_id)
        self.text = text
        self.voice = None
        self.photo = None
        self.video = None
        self.document = None
        self.sticker = None
        self.caption = None
        self.answers: list[str] = []

    async def answer(self, text: str, **_: object) -> None:
        self.answers.append(text)


@pytest.fixture()
def dummy_bot() -> DummyBot:
    return DummyBot()


@pytest.fixture()
def dummy_settings() -> SimpleNamespace:
    return SimpleNamespace(
        find_debounce_sec=0,
        jitsi_host="https://meet.jit.si",
        rate_limit_msg_per_sec=1.0,
    )
