import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.config.strings import (
    MSG_CHOOSE_ACTION,
    MSG_THINKING,
    MSG_TOO_LONG,
    MSG_UNAUTHORIZED,
    MSG_UNKNOWN_LANGUAGE,
)
from bot.handlers.auth import _is_authorized
from bot.handlers.utils import (
    LanguageNotDetectedException,
    TextTooLongException,
    close_active_messages,
    detect_and_get_actions,
)
from bot.keyboard import make_keyboard
from bot.session import UserSession

logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages from users.

    Deflect if message is too long. Otherwise, ask user to choose an action.
    """
    await update.effective_chat.send_action("typing")
    reply = await update.message.reply_text(
        text=MSG_THINKING,
        reply_markup=None,
        reply_to_message_id=update.message.message_id,
    )

    session = UserSession.from_context(context)
    user_id = update.effective_user.id if update.effective_user else None
    if not _is_authorized(user_id):
        logger.warning("Unauthorized access attempt by user=%s", user_id)
        await reply.edit_text(MSG_UNAUTHORIZED)
        return

    try:
        lang, action_types = await detect_and_get_actions(update.message.text)
    except TextTooLongException:
        await reply.edit_text(MSG_TOO_LONG)
        return
    except LanguageNotDetectedException:
        await reply.edit_text(MSG_UNKNOWN_LANGUAGE)
        return

    await close_active_messages(session, context.bot, update.effective_chat.id)

    await reply.edit_text(
        text=MSG_CHOOSE_ACTION,
        reply_markup=make_keyboard(action_types),
    )
    session.store_original_trigger_message(
        reply.message_id, update.message.text, lang, action_types,
    )
    session.add_active_message(reply.message_id)
