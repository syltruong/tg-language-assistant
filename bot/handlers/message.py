import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.config.strings import (
    MSG_CHOOSE_ACTION,
    MSG_TOO_LONG,
    MSG_UNAUTHORIZED,
    MSG_UNKNOWN_LANGUAGE,
)
from bot.handlers.auth import _is_authorized
from bot.keyboard import make_keyboard
from bot.language import detect_language
from bot.session import UserSession
from bot.types import ActionType

logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages from users. Deflect if message is too long. Else, ask user to choose an action."""
    session = UserSession.from_context(context)
    user_id = update.effective_user.id if update.effective_user else None
    if not _is_authorized(user_id):
        logger.warning("Unauthorized access attempt by user=%s", user_id)
        await update.message.reply_text(MSG_UNAUTHORIZED)
        return

    await update.effective_chat.send_action("typing")

    if len(update.message.text) > 100:
        await update.message.reply_text(
            MSG_TOO_LONG,
            reply_to_message_id=update.message.message_id,
        )
        return

    # This line runs the detect_language function in a separate thread, avoiding blocking the main event loop for replies to other users
    loop = asyncio.get_running_loop()
    lang = await loop.run_in_executor(None, detect_language, update.message.text)
    if lang is None:
        await update.message.reply_text(
            MSG_UNKNOWN_LANGUAGE,
            reply_to_message_id=update.message.message_id,
        )
        return

    action_types = [ActionType.TRANSLATE] if lang == "source" else [ ActionType.TRANSLATE,
    ActionType.ANALYZE,
    ActionType.REPLY,
    ActionType.CORRECT,]
    reply = await update.message.reply_text(
        text=MSG_CHOOSE_ACTION,
        reply_markup=make_keyboard(action_types),
        reply_to_message_id=update.message.message_id,
    )
    session.store_original_trigger_message(reply.message_id, update.message.text, lang, action_types)
