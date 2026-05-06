import html
import json

from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes

from bot.config.lang import SUPPORTED_LANGUAGES
from bot.config.messages import MsgAiError, MsgUnknownLanguage, MsgWantToGoDeeper, t
from bot.handlers_v2.keyboard import KEYBOARD
from bot.handlers_v2.response import send_response, stream_response
from bot.llm import LLMClient
from bot.prompts_v2 import INSTANT_PROMPTS, SYSTEM_PROMPT
from bot.routing.local import (
    UserFacingError,
    detect_language,
    filter_telegram_message,
)
from bot.session import UserSession
from bot.types import InstantActionType


class MessageHandlerService:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

        lang = detect_language(text, list(SUPPORTED_LANGUAGES.keys()))

        if lang == base_language:
            await self._handle_message_in_base_language(update, context, session)
        elif lang == target_language:
            await self._handle_message_in_target_language(update, context, session)
        else:
            await update.message.reply_text(t(MsgUnknownLanguage, base_language))
            return

    async def _handle_message_in_base_language(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        session: UserSession,
    ) -> None:
        text = update.message.text.strip()

        system_prompt = SYSTEM_PROMPT.format(
            base_language=session.base_language_name,
            target_language=session.target_language_name,
        )
        user_prompt = INSTANT_PROMPTS[InstantActionType.TRANSLATE].format(
            from_language=session.base_language_name,
            to_language=session.target_language_name,
            text=text,
        )

        try:
            stream = await self._llm.stream(system_prompt, user_prompt)
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
            result = await self._llm.complete(system=system_prompt, user=user_prompt)
            await send_response(
                bot=context.bot,
                chat_id=update.effective_chat.id,
                text=result,
                reply_to_message_id=update.message.message_id,
            )

    async def _handle_message_in_target_language(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        session: UserSession,
    ) -> None:
        text = update.message.text.strip()

        system_prompt = SYSTEM_PROMPT.format(
            base_language=session.base_language_name,
            target_language=session.target_language_name,
        )
        user_prompt = INSTANT_PROMPTS[InstantActionType.TRANSLATE_WITH_CONTEXT].format(
            from_language=session.target_language_name,
            to_language=session.base_language_name,
            text=text,
        )

        raw = await self._llm.complete(system=system_prompt, user=user_prompt)
        try:
            result = json.loads(raw)
            translation = result["translation"]
            one_line_context = result["one_line_context"]
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("translate_with_context returned unexpected output: %s", e)
            await update.message.reply_text(
                t(MsgAiError, session.base_language, error=str(e))
            )
            return

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
            reply_markup=KEYBOARD,
        )
