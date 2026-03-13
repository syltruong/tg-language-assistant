from telegram import Update
from telegram.ext import ContextTypes

from bot.config.messages import DEFAULT_LOCALE, MsgChooseAction, t
from bot.routing.local import (
    SUPPORTED_LANGUAGES,
    UserFacingError,
    detect_language,
    filter_telegram_text_message,
)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages.

    Validates the message, detects its language, and replies.
    """
    # TODO: allow user to set locale in the /start menu
    locale = DEFAULT_LOCALE

    await update.effective_chat.send_action("typing")

    try:
        filter_telegram_text_message(update.message)
    except UserFacingError as exc:
        await update.message.reply_text(t(type(exc), locale))
        return

    text = update.message.text.strip()
    lang = detect_language(text, SUPPORTED_LANGUAGES)

    await update.message.reply_text(t(MsgChooseAction, locale))
