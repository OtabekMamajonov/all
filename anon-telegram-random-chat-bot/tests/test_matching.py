from __future__ import annotations

import asyncio

from app.matching import MatchingService
from app.storage import Storage


def test_matching_pairs_two_users(matching: MatchingService) -> None:
    async def scenario() -> None:
        result1 = await matching.enqueue(1)
        assert result1.status == "waiting"
        result2 = await matching.enqueue(2)
        assert result2.status == "matched"
        assert result2.partner_id == 1
        session1 = await matching.get_session(1)
        session2 = await matching.get_session(2)
        assert session1 is not None
        assert session2 is not None
        assert session1.partner_id == 2
        assert session2.partner_id == 1
        assert session1.session_id == session2.session_id

    asyncio.run(scenario())


def test_matching_respects_blocklist(matching: MatchingService, storage: Storage) -> None:
    async def scenario() -> None:
        await storage.add_block(1, 2)
        await matching.enqueue(1)
        await matching.enqueue(2)
        assert await matching.is_waiting(1)
        assert await matching.is_waiting(2)
        result = await matching.enqueue(3)
        assert result.status == "matched"
        assert result.partner_id in {1, 2}

    asyncio.run(scenario())
