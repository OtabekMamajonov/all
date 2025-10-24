from __future__ import annotations

from app.i18n import gettext as _
from app.matching import MatchingService
from app.utils.compat import Bot, TelegramAPIError
from app.utils.logging import get_logger
from app.utils.ratelimit import RateLimiter

LOGGER = get_logger(__name__)


async def relay_message(
    message,
    matching: MatchingService,
    bot: Bot,
    rate_limiter: RateLimiter,
    rate: float,
) -> None:
    user_id = getattr(getattr(message, "from_user", None), "id", None)
    if user_id is None:
        return
    allowed = await rate_limiter.allow(f"msg:{user_id}", rate, burst=2)
    if not allowed:
        await message.answer(_("relay.rate_limited"))
        return
    session = await matching.get_session(user_id)
    if session is None:
        await message.answer(_("relay.no_session"))
        return
    partner_id = session.partner_id
    try:
        delivered = await _send_to_partner(bot, message, partner_id)
    except TelegramAPIError as exc:  # pragma: no cover - network dependent
        LOGGER.warning("Failed to relay message to %s: %s", partner_id, exc)
        await message.answer(_("error.generic"))
        return
    if not delivered:
        await message.answer(_("relay.unsupported"))


async def _send_to_partner(bot: Bot, message, partner_id: int) -> bool:
    if getattr(message, "text", None):
        await bot.send_message(chat_id=partner_id, text=message.text)  # type: ignore[attr-defined]
        return True
    if getattr(message, "voice", None):
        await bot.send_voice(chat_id=partner_id, voice=message.voice.file_id)  # type: ignore[attr-defined]
        return True
    if getattr(message, "photo", None):
        photo = message.photo[-1].file_id  # type: ignore[index]
        caption = getattr(message, "caption", None)
        await bot.send_photo(  # type: ignore[attr-defined]
            chat_id=partner_id,
            photo=photo,
            caption=caption or None,
        )
        return True
    if getattr(message, "video", None):
        caption = getattr(message, "caption", None)
        await bot.send_video(  # type: ignore[attr-defined]
            chat_id=partner_id,
            video=message.video.file_id,
            caption=caption or None,
        )
        return True
    if getattr(message, "document", None):
        caption = getattr(message, "caption", None)
        await bot.send_document(  # type: ignore[attr-defined]
            chat_id=partner_id,
            document=message.document.file_id,
            caption=caption or None,
        )
        return True
    if getattr(message, "sticker", None):
        await bot.send_sticker(chat_id=partner_id, sticker=message.sticker.file_id)  # type: ignore[attr-defined]
        return True
    return False
