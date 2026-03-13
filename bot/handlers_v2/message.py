from telegram import Update
from telegram.ext import ContextTypes

from bot.config.messages import DEFAULT_LOCALE, t, MsgUnknownLanguage
from bot.routing.local import SUPPORTED_LANGUAGES, UserFacingError, detect_language, filter_telegram_text_message


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages.

    Validates the message, detects its language, and replies.
    """
    # TODO: allow user to set locale in the /start menu and retrieve from context.user_data
    locale = DEFAULT_LOCALE
    target_language = "fr"

    await update.effective_chat.send_action("typing")

    try:
        filter_telegram_text_message(update.message)
    except UserFacingError as exc:
        await update.message.reply_text(t(type(exc), locale))
        return

    text = update.message.text.strip()
    lang = detect_language(text, list(SUPPORTED_LANGUAGES.keys()))

    if lang == locale:
        await _handle_message_in_ui_language(update, context)
    elif lang == target_language:
        await _handle_message_in_target_language(update, context)
    else:
        await update.message.reply_text(t(MsgUnknownLanguage, locale))
        return

async def _handle_message_in_ui_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass

async def _handle_message_in_target_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass
