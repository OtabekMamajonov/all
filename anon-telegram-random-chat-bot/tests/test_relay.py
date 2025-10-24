from __future__ import annotations

import asyncio

from app.matching import MatchingService
from app.relay import relay_message
from app.storage import Storage
from app.utils.ratelimit import RateLimiter
from tests.conftest import DummyBot, DummyMessage


def test_relay_text_message(
    matching: MatchingService,
    storage: Storage,
    rate_limiter: RateLimiter,
    dummy_bot: DummyBot,
) -> None:
    async def scenario() -> None:
        await storage.create_session(1, 2, "sess-1")
        message = DummyMessage(user_id=1, text="hello")
        await relay_message(message, matching, dummy_bot, rate_limiter, rate=1.0)
        assert dummy_bot.sent == [("message", 2, "hello")]

    asyncio.run(scenario())


def test_relay_requires_active_session(
    matching: MatchingService,
    rate_limiter: RateLimiter,
    dummy_bot: DummyBot,
) -> None:
    async def scenario() -> None:
        message = DummyMessage(user_id=5, text="ping")
        await relay_message(message, matching, dummy_bot, rate_limiter, rate=1.0)
        assert message.answers[-1].startswith("You are not matched")

    asyncio.run(scenario())
