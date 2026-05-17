"""KeyboardTrigger — coordinates the Keyboard Action flow."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.actions.registry import ActionRegistry
from bot.gateway import AnchorMessage, LanguageRole
from bot.keyboard import KEYBOARD, SELECT_PREFIX, build_suggestions_keyboard
from bot.publisher import ResponsePublisher
from bot.runner import ActionRunner
from bot.session import UserSession
from bot.types import FormattedResult


class KeyboardTrigger:
    def __init__(
        self,
        registry: ActionRegistry,
        runner: ActionRunner,
        publisher: ResponsePublisher,
    ) -> None:
        self._registry = registry
        self._runner = runner
        self._publisher = publisher

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

        await update.effective_chat.send_action("typing")

        query = update.callback_query
        await query.answer()

        session = UserSession.from_context(context)

        if query.data.startswith(SELECT_PREFIX):
            await self._handle_selection(query, session)
            return

        language_pair = session.language_pair
        replied = getattr(query.message, "reply_to_message", None)
        text = (getattr(replied, "text", "") or "").strip()

        action_type = query.data
        action = self._registry.get(action_type)

        # Keyboard actions operate on messages in the target language by default.
        # Use stored detected language if available, else assume target.
        msg_id = query.message.message_id
        detected_lang = session.get_detected_language(msg_id) or language_pair.target
        role = (
            LanguageRole.TARGET
            if detected_lang == language_pair.target
            else LanguageRole.BASE
        )

        anchor = AnchorMessage(
            text=text,
            detected_language=detected_lang,
            language_role=role,
        )

        result = await self._runner.run(action, anchor, language_pair)

        if result.suggestions:
            session.store_suggestions(msg_id, result.suggestions)
            reply_markup = build_suggestions_keyboard(result.suggestions)
        else:
            reply_markup = KEYBOARD

        await self._publisher.edit_slot(
            result=result,
            chat_id=query.message.chat.id,
            slot_id=msg_id,
            session=session,
            reply_markup=reply_markup,
        )

    async def _handle_selection(self, query, session: UserSession) -> None:
        index = int(query.data[len(SELECT_PREFIX):])
        msg_id = query.message.message_id
        replies = session.get_suggestions(msg_id)

        if not replies or index >= len(replies):
            return

        result = FormattedResult(text=replies[index].text, parse_mode=None)

        await self._publisher.edit_slot(
            result=result,
            chat_id=query.message.chat.id,
            slot_id=msg_id,
            session=session,
            reply_markup=KEYBOARD,
            user_id=query.from_user.id,
        )
