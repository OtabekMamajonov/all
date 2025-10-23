from __future__ import annotations

import asyncio
import math
import time
from dataclasses import dataclass
from typing import Dict, Optional, Protocol, Tuple

try:
    import redis.asyncio as redis
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    redis = None


class RateLimitBackend(Protocol):
    async def allow(self, key: str, rate: float, burst: int) -> bool:
        ...

    async def debounce(self, key: str, cooldown: float) -> bool:
        ...

    async def close(self) -> None:
        ...


@dataclass
class RateLimiter:
    backend: RateLimitBackend

    @classmethod
    async def create(cls, redis_url: Optional[str]) -> "RateLimiter":
        if redis_url and redis is not None:
            backend = RedisRateLimitBackend(redis_url)
            await backend.init()
        else:
            backend = InMemoryRateLimitBackend()
        return cls(backend=backend)

    async def allow(self, key: str, rate: float, burst: int = 1) -> bool:
        if rate <= 0:
            return False
        return await self.backend.allow(key, rate, burst)

    async def debounce(self, key: str, cooldown: float) -> bool:
        if cooldown <= 0:
            return True
        return await self.backend.debounce(key, cooldown)

    async def close(self) -> None:
        await self.backend.close()


class InMemoryRateLimitBackend:
    def __init__(self) -> None:
        self._allow_state: Dict[str, Tuple[float, float]] = {}
        self._debounce_state: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def allow(self, key: str, rate: float, burst: int) -> bool:
        now = time.monotonic()
        async with self._lock:
            tokens, last_ts = self._allow_state.get(key, (float(burst), now))
            tokens = min(float(burst), tokens + (now - last_ts) * rate)
            allowed = False
            if tokens >= 1:
                tokens -= 1
                allowed = True
            self._allow_state[key] = (tokens, now)
            return allowed

    async def debounce(self, key: str, cooldown: float) -> bool:
        now = time.monotonic()
        async with self._lock:
            expires_at = self._debounce_state.get(key)
            if expires_at and expires_at > now:
                return False
            self._debounce_state[key] = now + cooldown
            return True

    async def close(self) -> None:  # pragma: no cover - nothing to close
        self._allow_state.clear()
        self._debounce_state.clear()


class RedisRateLimitBackend:
    def __init__(self, url: str) -> None:
        if redis is None:  # pragma: no cover - guarded at factory level
            raise RuntimeError("redis library is not available")
        self._url = url
        self._client: Optional[redis.Redis] = None
        self._allow_script: Optional[redis.client.Script] = None

    async def init(self) -> None:
        assert redis is not None  # for type checkers
        self._client = redis.from_url(self._url, decode_responses=True)
        script = """
        local key = KEYS[1]
        local rate = tonumber(ARGV[1])
        local burst = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        local ttl = tonumber(ARGV[4])
        local data = redis.call('HMGET', key, 'tokens', 'ts')
        local tokens = tonumber(data[1])
        local ts = tonumber(data[2])
        if tokens == nil then
            tokens = burst
            ts = now
        else
            local delta = now - ts
            if delta > 0 then
                tokens = math.min(burst, tokens + delta * rate)
            end
        end
        local allowed = 0
        if tokens >= 1 then
            tokens = tokens - 1
            allowed = 1
        end
        redis.call('HMSET', key, 'tokens', tokens, 'ts', now)
        redis.call('EXPIRE', key, ttl)
        return allowed
        """
        self._allow_script = self._client.register_script(script)

    async def allow(self, key: str, rate: float, burst: int) -> bool:
        if self._client is None or self._allow_script is None:  # pragma: no cover
            raise RuntimeError("Rate limiter not initialized")
        ttl = max(1, int(math.ceil(float(burst) / rate * 2)))
        now = time.monotonic()
        allowed = await self._allow_script(
            keys=[f"rl:allow:{key}"],
            args=[rate, burst, now, ttl],
        )
        return bool(int(allowed))

    async def debounce(self, key: str, cooldown: float) -> bool:
        if self._client is None:  # pragma: no cover
            raise RuntimeError("Rate limiter not initialized")
        ttl = max(1, int(math.ceil(cooldown)))
        return bool(
            await self._client.set(
                name=f"rl:debounce:{key}",
                value="1",
                ex=ttl,
                nx=True,
            )
        )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            try:  # pragma: no cover - compatibility across redis versions
                await self._client.wait_closed()
            except AttributeError:
                pass
            self._client = None
            self._allow_script = None
