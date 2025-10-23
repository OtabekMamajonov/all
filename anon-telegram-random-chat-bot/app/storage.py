from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional, Sequence, Tuple

try:
    import aiosqlite
except ModuleNotFoundError:  # pragma: no cover - fallback for tests
    aiosqlite = None
    import sqlite3

    class _AsyncCursor:
        def __init__(self, cursor: sqlite3.Cursor) -> None:
            self._cursor = cursor

        async def fetchone(self) -> Optional[sqlite3.Row]:
            return await asyncio.to_thread(self._cursor.fetchone)

        async def fetchall(self) -> list[sqlite3.Row]:
            return await asyncio.to_thread(self._cursor.fetchall)

        async def __aenter__(self) -> "_AsyncCursor":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            await asyncio.to_thread(self._cursor.close)

    class _AsyncConnection:
        def __init__(self, conn: sqlite3.Connection) -> None:
            self._conn = conn

        async def executescript(self, script: str) -> None:
            await asyncio.to_thread(self._conn.executescript, script)

        async def execute(self, query: str, params: Sequence[Any] | None = None) -> _AsyncCursor:
            params = params or []
            cursor = await asyncio.to_thread(self._conn.execute, query, params)
            return _AsyncCursor(cursor)

        async def executemany(self, query: str, seq_of_params: Sequence[Sequence[Any]]) -> None:
            await asyncio.to_thread(self._conn.executemany, query, seq_of_params)

        async def commit(self) -> None:
            await asyncio.to_thread(self._conn.commit)

        async def close(self) -> None:
            await asyncio.to_thread(self._conn.close)

        @property
        def row_factory(self) -> Any:
            return self._conn.row_factory

        @row_factory.setter
        def row_factory(self, value: Any) -> None:
            self._conn.row_factory = value

    async def _connect(path: Path) -> _AsyncConnection:
        conn = sqlite3.connect(path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return _AsyncConnection(conn)
else:
    from aiosqlite import Row  # type: ignore[attr-defined]

    async def _connect(path: Path):
        conn = await aiosqlite.connect(path)
        conn.row_factory = aiosqlite.Row
        return conn

from .utils.ids import mask_user_id
from .utils.logging import get_logger


@dataclass
class SessionRecord:
    user_id: int
    partner_id: int
    session_id: str
    started_at: datetime


@dataclass
class SessionEnd:
    session_id: str
    users: Tuple[int, int]


class Storage:
    def __init__(self, db_path: str, session_ttl: int = 0, mask_reports: bool = True, mask_salt: Optional[str] = None) -> None:
        self._db_path = Path(db_path)
        self._session_ttl = session_ttl
        self._mask_reports = mask_reports
        self._mask_salt = mask_salt
        self._conn: Optional[Any] = None
        self._lock = asyncio.Lock()
        self._logger = get_logger(__name__)

    async def init(self) -> None:
        if not self._db_path.parent.exists():
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await _connect(self._db_path)
        await self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                user_id INTEGER PRIMARY KEY,
                partner_id INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                started_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS session_meta (
                session_id TEXT PRIMARY KEY,
                user1 INTEGER NOT NULL,
                user2 INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT
            );
            CREATE TABLE IF NOT EXISTS blocked_pairs (
                blocker INTEGER NOT NULL,
                blocked INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(blocker, blocked)
            );
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                reporter TEXT NOT NULL,
                reported TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        await self._conn.commit()
        await self.cleanup_expired_sessions()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def create_session(self, user_a: int, user_b: int, session_id: str) -> None:
        if self._conn is None:
            raise RuntimeError("Storage not initialized")
        now = self._now().isoformat()
        async with self._lock:
            await self._conn.executemany(
                "INSERT OR REPLACE INTO sessions (user_id, partner_id, session_id, started_at) VALUES (?, ?, ?, ?)",
                [
                    (user_a, user_b, session_id, now),
                    (user_b, user_a, session_id, now),
                ],
            )
            await self._conn.execute(
                "INSERT OR REPLACE INTO session_meta (session_id, user1, user2, started_at, ended_at) VALUES (?, ?, ?, ?, NULL)",
                (session_id, user_a, user_b, now),
            )
            await self._conn.commit()

    async def get_session(self, user_id: int) -> Optional[SessionRecord]:
        if self._conn is None:
            raise RuntimeError("Storage not initialized")
        async with self._lock:
            cursor = await self._conn.execute(
                "SELECT partner_id, session_id, started_at FROM sessions WHERE user_id = ?",
                (user_id,),
            )
            async with cursor:
                row = await cursor.fetchone()
        if row is None:
            return None
        return SessionRecord(
            user_id=user_id,
            partner_id=row["partner_id"],
            session_id=row["session_id"],
            started_at=datetime.fromisoformat(row["started_at"]),
        )

    async def end_session(self, user_id: int) -> Optional[SessionEnd]:
        if self._conn is None:
            raise RuntimeError("Storage not initialized")
        async with self._lock:
            cursor = await self._conn.execute(
                "SELECT session_id FROM sessions WHERE user_id = ?",
                (user_id,),
            )
            async with cursor:
                row = await cursor.fetchone()
            if row is None:
                return None
            session_id = row["session_id"]
            cursor = await self._conn.execute(
                "SELECT user_id FROM sessions WHERE session_id = ?",
                (session_id,),
            )
            async with cursor:
                members = [r["user_id"] for r in await cursor.fetchall()]
            if len(members) != 2:
                self._logger.warning("Session %s has %d members", session_id, len(members))
            await self._conn.execute(
                "DELETE FROM sessions WHERE session_id = ?",
                (session_id,),
            )
            await self._conn.execute(
                "UPDATE session_meta SET ended_at = ? WHERE session_id = ?",
                (self._now().isoformat(), session_id),
            )
            await self._conn.commit()
        users: Tuple[int, int]
        if len(members) == 2:
            users = (members[0], members[1])
        elif len(members) == 1:
            users = (members[0], user_id)
        else:
            users = (user_id, user_id)
        return SessionEnd(session_id=session_id, users=users)

    async def is_blocked(self, user_a: int, user_b: int) -> bool:
        if self._conn is None:
            raise RuntimeError("Storage not initialized")
        async with self._lock:
            cursor = await self._conn.execute(
                "SELECT 1 FROM blocked_pairs WHERE blocker = ? AND blocked = ?",
                (user_a, user_b),
            )
            async with cursor:
                return await cursor.fetchone() is not None

    async def add_block(self, user_a: int, user_b: int) -> None:
        if self._conn is None:
            raise RuntimeError("Storage not initialized")
        now = self._now().isoformat()
        pairs = [(user_a, user_b, now), (user_b, user_a, now)]
        async with self._lock:
            await self._conn.executemany(
                "INSERT OR IGNORE INTO blocked_pairs (blocker, blocked, created_at) VALUES (?, ?, ?)",
                pairs,
            )
            await self._conn.commit()

    async def add_report(self, session_id: str, reporter_id: int, reported_id: int) -> None:
        if self._conn is None:
            raise RuntimeError("Storage not initialized")
        if self._mask_reports:
            reporter = mask_user_id(reporter_id, self._mask_salt)
            reported = mask_user_id(reported_id, self._mask_salt)
        else:
            reporter = str(reporter_id)
            reported = str(reported_id)
        async with self._lock:
            await self._conn.execute(
                "INSERT INTO reports (session_id, reporter, reported, created_at) VALUES (?, ?, ?, ?)",
                (session_id, reporter, reported, self._now().isoformat()),
            )
            await self._conn.commit()

    async def cleanup_expired_sessions(self) -> None:
        if self._conn is None:
            raise RuntimeError("Storage not initialized")
        if self._session_ttl <= 0:
            return
        cutoff = self._now() - timedelta(seconds=self._session_ttl)
        async with self._lock:
            await self._conn.execute(
                "DELETE FROM session_meta WHERE ended_at IS NOT NULL AND ended_at < ?",
                (cutoff.isoformat(),),
            )
            await self._conn.commit()

    async def remove_waiting_users(self, users: Sequence[int]) -> None:
        if not users or self._conn is None:
            return
        placeholders = ",".join("?" for _ in users)
        async with self._lock:
            await self._conn.execute(
                f"DELETE FROM sessions WHERE user_id IN ({placeholders})",
                tuple(users),
            )
            await self._conn.commit()

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)
