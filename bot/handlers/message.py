import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.keyboard import make_keyboard
from bot.language import detect_language
from bot.session import UserSession
from bot.config.strings import MSG_TOO_LONG, MSG_CHOOSE_ACTION, MSG_UNKNOWN_LANGUAGE, MSG_UNAUTHORIZED
from bot.types import KeyboardMode
from bot.handlers.auth import _is_authorized

logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages from users. Deflect if message is too long. Else, ask user to choose an action."""
    session = UserSession.from_context(context)
    user_id = update.effective_user.id if update.effective_user else None
    if not _is_authorized(user_id):
        logger.warning("Unauthorized access attempt by user=%s", user_id)
        await update.message.reply_text(MSG_UNAUTHORIZED)
        return

    if len(update.message.text) > 100:
        await update.message.reply_text(
            MSG_TOO_LONG,
            reply_to_message_id=update.message.message_id,
        )
        return

    lang = detect_language(update.message.text)
    if lang is None:
        await update.message.reply_text(
            MSG_UNKNOWN_LANGUAGE,
            reply_to_message_id=update.message.message_id,
        )
        return

    mode = KeyboardMode.TRANSLATE_ONLY if lang == "source" else KeyboardMode.FULL

    reply = await update.message.reply_text(
        text=MSG_CHOOSE_ACTION,
        reply_markup=make_keyboard(mode),
        reply_to_message_id=update.message.message_id,
    )
    session.store_message(reply.message_id, update.message.text, mode)
