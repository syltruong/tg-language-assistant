from telegram import Update
from telegram.ext import ContextTypes

from bot.config.messages import t, MsgUnknownLanguage
from bot.handlers_v2.response import send_response, stream_response
from bot.llm import get_completion, stream_completion
from bot.config.lang import LANGUAGE_NAMES, SUPPORTED_LANGUAGES
from bot.routing.local import (
    UserFacingError,
    detect_language,
    filter_telegram_message,
)
from bot.session import UserSession

from bot.prompts_v2 import PROMPTS, SYSTEM_PROMPT
from bot.types import ActionType

from loguru import logger


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages.

    Validates the message, detects its language, and replies.
    """
    session = UserSession.from_context(context)
    base_language = session.base_language
    target_language = session.target_language

    await update.effective_chat.send_action("typing")

    try:
        filter_telegram_message(update)
    except UserFacingError as exc:
        await update.message.reply_text(t(type(exc), base_language))
        return

    text = update.message.text.strip()

    # Note: the language detection is very crude.
    # LLM-backed subsequent steps need to take into account the language detection is not perfect.
    lang = detect_language(text, list(SUPPORTED_LANGUAGES.keys()))

    if lang == base_language:
        await _handle_message_in_base_language(update, context)
    elif lang == target_language:
        await _handle_message_in_target_language(update, context)
    else:
        await update.message.reply_text(t(MsgUnknownLanguage, base_language))
        return


async def _handle_message_in_base_language(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle message in UI language.
    1. Translate message to target language
    2. Send translated message to user

    Prompt idea: confirm the language of the message and translate it to the target language.
    """

    # TODO: optimise and avoid calling UserSession.from_context(context) multiple times
    session = UserSession.from_context(context)
    base_language = session.base_language
    target_language = session.target_language

    text = update.message.text.strip()

    base_name = LANGUAGE_NAMES[base_language]
    target_name = LANGUAGE_NAMES[target_language]

    system_prompt = SYSTEM_PROMPT.format(
        base_language=base_name, target_language=target_name
    )
    user_prompt = PROMPTS[ActionType.TRANSLATE].format(
        base_language=base_name, target_language=target_name, text=text
    )

    try:
        stream = stream_completion(system_prompt, user_prompt)
        await stream_response(
            bot=context.bot,
            chat_id=update.effective_chat.id,
            stream=stream,
            reply_to_message_id=update.message.message_id,
        )
    except Exception as e:
        logger.warning(
            "Streaming failed, falling back to non-streaming: %s",
            e,
        )
        result = await get_completion(system_prompt, user_prompt)
        await send_response(
            bot=context.bot,
            chat_id=update.effective_chat.id,
            text=result,
            reply_to_message_id=update.message.message_id,
        )

async def _handle_message_in_target_language(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle message in target language.
    1. Translate message to UI language
    2. Infer a one-line context
    3. Reply with keyboard markup
    """

    pass
