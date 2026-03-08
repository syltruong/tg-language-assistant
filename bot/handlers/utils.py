import asyncio
import logging

from telegram import Bot

from bot.keyboard import REOPEN_KEYBOARD
from bot.language import detect_language
from bot.session import UserSession
from bot.types import ActionType

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 100

class TextTooLongException(Exception):
    pass

class LanguageNotDetectedException(Exception):
    pass

async def close_active_messages(
    session: UserSession, bot: Bot, chat_id: int,
) -> None:
    """Replace the keyboard on all tracked active messages with [Reopen]."""
    for msg_id in session.get_active_messages():
        try:
            await bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=msg_id,
                reply_markup=REOPEN_KEYBOARD,
            )
        except Exception:
            logger.debug("Could not update keyboard for message %s", msg_id)


async def detect_and_get_actions(
    text: str,
) -> tuple[str, list[ActionType]]:
    """Detect language and derive available action types.

    Returns ``(lang, action_types)``.

    Raises:
        TextTooLongException: If *text* exceeds ``MAX_MESSAGE_LENGTH``.
        LanguageNotDetectedException: If the language detector cannot
            classify *text* as French or English.
    """
    if len(text) > MAX_MESSAGE_LENGTH:
        raise TextTooLongException(text)

    loop = asyncio.get_running_loop()
    lang = await loop.run_in_executor(None, detect_language, text)
    if lang is None:
        raise LanguageNotDetectedException(text)
    action_types = (
        [ActionType.TRANSLATE]
        if lang == "source"
        else [
            ActionType.TRANSLATE,
            ActionType.ANALYZE,
            ActionType.REPLY,
            ActionType.CORRECT,
        ]
    )
    return lang, action_types
