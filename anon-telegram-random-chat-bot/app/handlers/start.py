from __future__ import annotations

from ..config import Settings
from ..i18n import gettext as _
from ..keyboards import main_menu
from ..utils.compat import Command, CommandStart, Router

router = Router()


@router.message(CommandStart())
async def handle_start(message, settings: Settings) -> None:
    await message.answer(
        text=f"{_('start.greeting')}\n{_('start.instructions')}\n{_('start.privacy')}",
        reply_markup=main_menu(),
    )


@router.message(Command("help"))
async def handle_help(message) -> None:
    await message.answer(_("help.text"))
