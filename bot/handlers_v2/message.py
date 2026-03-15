import html
import json

from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes

from bot.config.lang import SUPPORTED_LANGUAGES
from bot.config.messages import MsgUnknownLanguage, MsgWantToGoDeeper, t
from bot.handlers_v2.response import send_response, stream_response
from bot.llm import get_completion, stream_completion
from bot.prompts_v2 import PROMPTS, SYSTEM_PROMPT
from bot.routing.local import (
    UserFacingError,
    detect_language,
    filter_telegram_message,
)
from bot.session import UserSession
from bot.types import ActionType


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
    # LLM-backed steps must account for imperfect language detection.
    lang = detect_language(text, list(SUPPORTED_LANGUAGES.keys()))

    if lang == base_language:
        await _handle_message_in_base_language(update, context, session)
    elif lang == target_language:
        await _handle_message_in_target_language(update, context, session)
    else:
        await update.message.reply_text(t(MsgUnknownLanguage, base_language))
        return


async def _handle_message_in_base_language(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session: UserSession,
) -> None:
    """
    Handle message in UI language.
    1. Translate message to target language
    2. Send translated message to user

    Prompt idea: confirm message language, then translate to target.
    """
    text = update.message.text.strip()

    system_prompt = SYSTEM_PROMPT.format(
        base_language=session.base_language_name,
        target_language=session.target_language_name,
    )
    user_prompt = PROMPTS[ActionType.TRANSLATE].format(
        from_language=session.base_language_name,
        to_language=session.target_language_name,
        text=text,
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
        # TODO: check that if stream_response raises an exception, the fallback is able to
        # override the in-progress message with a new message.
        logger.warning(
            "Streaming failed, falling back to non-streaming: %s",
            e,
        )
        result = await get_completion(system_prompt=system_prompt, user_prompt=user_prompt)
        await send_response(
            bot=context.bot,
            chat_id=update.effective_chat.id,
            text=result,
            reply_to_message_id=update.message.message_id,
        )


async def _handle_message_in_target_language(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session: UserSession,
) -> None:
    """
    Handle message in target language.
    1. Translate message to UI language
    2. Infer a one-line context
    3. Reply with keyboard markup
    """

    text = update.message.text.strip()

    system_prompt = SYSTEM_PROMPT.format(
        base_language=session.base_language_name,
        target_language=session.target_language_name,
    )
    user_prompt = PROMPTS[ActionType.TRANSLATE_WITH_CONTEXT].format(
        from_language=session.target_language_name,
        to_language=session.base_language_name,
        text=text,
    )

    # TODO: handle LLM not returning valid JSON
    result = json.loads(
        await get_completion(system_prompt=system_prompt, user_prompt=user_prompt)
    )
    translation = result["translation"]
    one_line_context = result["one_line_context"]

    formatted = (
        f"<blockquote>{html.escape(translation)}</blockquote>\n"
        f"👉 <i>{html.escape(one_line_context)}</i>\n\n"
        f"{t(MsgWantToGoDeeper, base_language=session.base_language)}"
    )
    await send_response(
        bot=context.bot,
        chat_id=update.effective_chat.id,
        text=formatted,
        reply_to_message_id=update.message.message_id,
        parse_mode="HTML",
    )
