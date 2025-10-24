from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
from typing import Deque, Optional

from .storage import SessionEnd, SessionRecord, Storage
from .utils.ids import generate_session_id


@dataclass
class MatchResult:
    status: str
    partner_id: Optional[int] = None
    session_id: Optional[str] = None


class MatchingService:
    def __init__(self, storage: Storage) -> None:
        self._storage = storage
        self._queue: Deque[int] = deque()
        self._lock = asyncio.Lock()

    async def enqueue(self, user_id: int) -> MatchResult:
        async with self._lock:
            if user_id in self._queue:
                return MatchResult(status="waiting")
            for idx, candidate in enumerate(list(self._queue)):
                if candidate == user_id:
                    return MatchResult(status="waiting")
                if await self._storage.is_blocked(user_id, candidate) or await self._storage.is_blocked(candidate, user_id):
                    continue
                self._queue.remove(candidate)
                session_id = generate_session_id()
                await self._storage.create_session(user_id, candidate, session_id)
                return MatchResult(status="matched", partner_id=candidate, session_id=session_id)
            self._queue.append(user_id)
            return MatchResult(status="waiting")

    async def cancel_waiting(self, user_id: int) -> bool:
        async with self._lock:
            try:
                self._queue.remove(user_id)
                return True
            except ValueError:
                return False

    async def get_session(self, user_id: int) -> Optional[SessionRecord]:
        return await self._storage.get_session(user_id)

    async def end_session(self, user_id: int) -> Optional[SessionEnd]:
        return await self._storage.end_session(user_id)

    async def queue_size(self) -> int:
        async with self._lock:
            return len(self._queue)

    async def is_waiting(self, user_id: int) -> bool:
        async with self._lock:
            return user_id in self._queue

    async def reset(self) -> None:
        async with self._lock:
            self._queue.clear()
