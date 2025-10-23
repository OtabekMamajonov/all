from __future__ import annotations

import asyncio
from contextlib import suppress
from typing import Optional

from .config import get_settings
from .handlers import commands, fallback, start
from .i18n import load_messages
from .matching import MatchingService
from .storage import Storage
from .utils.compat import Bot, DefaultBotProperties, Dispatcher
from .utils.logging import configure_logging, get_logger
from .utils.ratelimit import RateLimiter

LOGGER = get_logger(__name__)


async def _cleanup_worker(storage: Storage, interval: int) -> None:
    try:
        while True:
            await asyncio.sleep(interval)
            await storage.cleanup_expired_sessions()
    except asyncio.CancelledError:  # pragma: no cover - cooperative cancellation
        LOGGER.debug("Cleanup worker cancelled")
        raise


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    load_messages()

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=None))  # type: ignore[call-arg]
    storage = Storage(
        db_path=settings.database_path,
        session_ttl=settings.session_ttl_sec,
        mask_reports=settings.mask_user_ids,
        mask_salt=settings.mask_salt,
    )
    await storage.init()
    rate_limiter = await RateLimiter.create(settings.redis_url)
    matching = MatchingService(storage=storage)

    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(commands.router)
    dp.include_router(fallback.router)

    if hasattr(dp, "workflow_data"):
        dp.workflow_data.update(
            {
                "settings": settings,
                "matching": matching,
                "rate_limiter": rate_limiter,
                "storage": storage,
            }
        )
    else:  # pragma: no cover - stub fallback
        dp["settings"] = settings  # type: ignore[index]
        dp["matching"] = matching  # type: ignore[index]
        dp["rate_limiter"] = rate_limiter  # type: ignore[index]
        dp["storage"] = storage  # type: ignore[index]

    cleanup_task: Optional[asyncio.Task[None]] = None
    if settings.cleanup_interval_sec > 0 and settings.session_ttl_sec > 0:
        cleanup_task = asyncio.create_task(
            _cleanup_worker(storage, settings.cleanup_interval_sec)
        )

    try:
        await dp.start_polling(bot)
    finally:
        if cleanup_task:
            cleanup_task.cancel()
            with suppress(asyncio.CancelledError):
                await cleanup_task
        await rate_limiter.close()
        await storage.close()
        if hasattr(bot, "session"):
            await bot.session.close()  # type: ignore[attr-defined]


if __name__ == "__main__":
    asyncio.run(main())
