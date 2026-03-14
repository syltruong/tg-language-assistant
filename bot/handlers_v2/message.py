from telegram import Update
from telegram.ext import ContextTypes

from bot.config.messages import t, MsgUnknownLanguage
from bot.routing.local import SUPPORTED_LANGUAGES, UserFacingError, detect_language, filter_telegram_message


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages.

    Validates the message, detects its language, and replies.
    """
    # TODO: allow user to set locale in the /start menu and retrieve from context.user_data
    locale = "en"
    target_language = "fr"

    await update.effective_chat.send_action("typing")

    try:
        filter_telegram_message(update)
    except UserFacingError as exc:
        await update.message.reply_text(t(type(exc), locale))
        return

    text = update.message.text.strip()

    # Note: the language detection is very crude.
    # LLM-backed subsequent steps need to take into account the language detection is not perfect.
    lang = detect_language(text, list(SUPPORTED_LANGUAGES.keys()))

    if lang == locale:
        await _handle_message_in_ui_language(update, context)
    elif lang == target_language:
        await _handle_message_in_target_language(update, context)
    else:
        await update.message.reply_text(t(MsgUnknownLanguage, locale))
        return

async def _handle_message_in_ui_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle message in UI language.
    1. Translate message to target language
    2. Send translated message to user

    Prompt idea: confirm the language of the message and translate it to the target language.
    """
    
    pass

async def _handle_message_in_target_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle message in target language.
    1. Translate message to UI language
    2. Infer a one-line context
    3. Reply with keyboard markup
    """

    pass
