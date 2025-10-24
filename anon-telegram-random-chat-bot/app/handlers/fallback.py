from __future__ import annotations

from ..config import Settings
from ..matching import MatchingService
from ..relay import relay_message
from ..utils.compat import Bot, Router
from ..utils.ratelimit import RateLimiter

router = Router()


@router.message()
async def handle_fallback(
    message,
    matching: MatchingService,
    bot: Bot,
    rate_limiter: RateLimiter,
    settings: Settings,
) -> None:
    await relay_message(
        message=message,
        matching=matching,
        bot=bot,
        rate_limiter=rate_limiter,
        rate=settings.rate_limit_msg_per_sec,
    )
