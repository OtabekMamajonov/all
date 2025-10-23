from __future__ import annotations

import asyncio

from app.handlers.commands import handle_block, handle_end, handle_find
from app.i18n import gettext as _
from app.matching import MatchingService
from app.storage import Storage
from app.utils.ratelimit import RateLimiter
from tests.conftest import DummyBot, DummyMessage


def test_handle_end_idempotent(
    matching: MatchingService,
    storage: Storage,
    dummy_bot: DummyBot,
) -> None:
    async def scenario() -> None:
        await storage.create_session(1, 2, "sess-end")
        message = DummyMessage(user_id=1)
        await handle_end(message, matching, dummy_bot)
        assert any(_("end.success_you") in text for text in message.answers)
        await handle_end(message, matching, dummy_bot)
        assert message.answers[-1] == _("end.no_session")

    asyncio.run(scenario())


def test_handle_find_matches_partner(
    matching: MatchingService,
    dummy_bot: DummyBot,
    rate_limiter: RateLimiter,
    dummy_settings,
) -> None:
    async def scenario() -> None:
        user1 = DummyMessage(user_id=1)
        user2 = DummyMessage(user_id=2)
        await handle_find(user1, matching, rate_limiter, dummy_settings, dummy_bot)
        assert user1.answers[-1] == _("find.waiting")
        await handle_find(user2, matching, rate_limiter, dummy_settings, dummy_bot)
        assert user2.answers[-1] == _("find.matched_you")
        assert dummy_bot.sent[-1][0] == "message"

    asyncio.run(scenario())


def test_handle_block_adds_block(
    matching: MatchingService,
    storage: Storage,
    dummy_bot: DummyBot,
) -> None:
    async def scenario() -> None:
        await storage.create_session(5, 6, "sess-block")
        message = DummyMessage(user_id=5)
        await handle_block(message, matching, storage, dummy_bot)
        assert any(_("block.success") in text for text in message.answers)
        assert await storage.is_blocked(5, 6)

    asyncio.run(scenario())
