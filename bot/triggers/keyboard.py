"""KeyboardTrigger — coordinates the Keyboard Action flow."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.actions.registry import ActionRegistry
from bot.gateway import AnchorMessage, LanguageRole
from bot.keyboard import KEYBOARD
from bot.publisher import ResponsePublisher
from bot.runner import ActionRunner
from bot.session import UserSession


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

        await self._publisher.publish(
            result=result,
            chat_id=query.message.chat.id,
            reply_to_message_id=query.message.message_id,
            session=session,
        )

        await self._publisher.reattach_keyboard(
            chat_id=query.message.chat.id,
            message_id=query.message.message_id,
            reply_markup=KEYBOARD,
            session=session,
        )
