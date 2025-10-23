from __future__ import annotations

from ..config import Settings
from ..i18n import gettext as _
from ..matching import MatchResult, MatchingService
from ..storage import SessionEnd, Storage
from ..utils.compat import Bot, Command, Router
from ..utils.ids import build_jitsi_room
from ..utils.logging import get_logger
from ..utils.ratelimit import RateLimiter

router = Router()
LOGGER = get_logger(__name__)


def _other_user(end: SessionEnd, current: int) -> int:
    for user in end.users:
        if user != current:
            return user
    return current


def _safe_link(host: str, room: str) -> str:
    return f"{host.rstrip('/')}/{room}"


async def _notify(bot: Bot, user_id: int, text: str) -> None:
    try:
        await bot.send_message(chat_id=user_id, text=text)  # type: ignore[attr-defined]
    except Exception as exc:  # pragma: no cover - network dependent
        LOGGER.debug("Failed to notify %s: %s", user_id, exc)


@router.message(Command("find"))
async def handle_find(
    message,
    matching: MatchingService,
    rate_limiter: RateLimiter,
    settings: Settings,
    bot: Bot,
) -> None:
    user_id = getattr(getattr(message, "from_user", None), "id", None)
    if user_id is None:
        return
    if not await rate_limiter.debounce(f"find:{user_id}", settings.find_debounce_sec):
        await message.answer(_("find.cooldown"))
        return
    session = await matching.get_session(user_id)
    if session is not None:
        await message.answer(_("find.already_in_session"))
        return
    if await matching.is_waiting(user_id):
        await message.answer(_("find.already_waiting"))
        return
    result = await matching.enqueue(user_id)
    await _respond_to_match(message, bot, result, user_id)


async def _respond_to_match(message, bot: Bot, result: MatchResult, user_id: int) -> None:
    if result.status == "waiting":
        await message.answer(_("find.waiting"))
        return
    await message.answer(_("find.matched_you"))
    if result.partner_id is not None:
        await _notify(bot, result.partner_id, _("find.matched_partner"))


@router.message(Command("end"))
async def handle_end(message, matching: MatchingService, bot: Bot) -> None:
    user_id = getattr(getattr(message, "from_user", None), "id", None)
    if user_id is None:
        return
    if await matching.cancel_waiting(user_id):
        await message.answer(_("end.queue_left"))
        return
    end = await matching.end_session(user_id)
    if end is None:
        await message.answer(_("end.no_session"))
        return
    await message.answer(_("end.success_you"))
    partner_id = _other_user(end, user_id)
    if partner_id != user_id:
        await _notify(bot, partner_id, _("end.success_partner"))


@router.message(Command("next"))
async def handle_next(
    message,
    matching: MatchingService,
    bot: Bot,
) -> None:
    user_id = getattr(getattr(message, "from_user", None), "id", None)
    if user_id is None:
        return
    if await matching.cancel_waiting(user_id):
        await message.answer(_("next.auto"))
    else:
        end = await matching.end_session(user_id)
        if end is not None:
            await message.answer(_("next.auto"))
            partner_id = _other_user(end, user_id)
            if partner_id != user_id:
                await _notify(bot, partner_id, _("end.success_partner"))
        else:
            await message.answer(_("end.no_session"))
    result = await matching.enqueue(user_id)
    await _respond_to_match(message, bot, result, user_id)


@router.message(Command("block"))
async def handle_block(message, matching: MatchingService, storage: Storage, bot: Bot) -> None:
    user_id = getattr(getattr(message, "from_user", None), "id", None)
    if user_id is None:
        return
    session = await matching.get_session(user_id)
    if session is None:
        await message.answer(_("block.no_session"))
        return
    end = await matching.end_session(user_id)
    if end is None:
        await message.answer(_("block.no_session"))
        return
    partner_id = _other_user(end, user_id)
    await storage.add_block(user_id, partner_id)
    await message.answer(_("block.success"))
    if partner_id != user_id:
        await _notify(bot, partner_id, _("block.notify_partner"))


@router.message(Command("report"))
async def handle_report(message, matching: MatchingService, storage: Storage) -> None:
    user_id = getattr(getattr(message, "from_user", None), "id", None)
    if user_id is None:
        return
    session = await matching.get_session(user_id)
    if session is None:
        await message.answer(_("report.no_session"))
        return
    await storage.add_report(session.session_id, user_id, session.partner_id)
    await message.answer(_("report.thanks") + " " + _("report.logged", session_id=session.session_id))


@router.message(Command("video"))
async def handle_video(message, matching: MatchingService, settings: Settings, bot: Bot) -> None:
    user_id = getattr(getattr(message, "from_user", None), "id", None)
    if user_id is None:
        return
    session = await matching.get_session(user_id)
    if session is None:
        await message.answer(_("video.no_session"))
        return
    room = build_jitsi_room(session.session_id)
    link = _safe_link(settings.jitsi_host, room)
    text = _("video.link", link=link) + "\n" + _("video.expiry_note")
    await message.answer(text)
    partner_id = session.partner_id
    if partner_id != user_id:
        await _notify(bot, partner_id, text)
