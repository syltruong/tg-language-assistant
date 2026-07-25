"""MessageTrigger — coordinates the Instant Action flow."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.actions.registry import ActionRegistry
from bot.errors import UserFacingError
from bot.gateway import MessageGateway
from bot.keyboard import KEYBOARD
from bot.localizer import Localizer
from bot.publisher import ResponsePublisherProtocol
from bot.runner import ActionRunner
from bot.session import UserSession
from bot.types import ActionType


class MessageTrigger:
    def __init__(
        self,
        gateway: MessageGateway,
        registry: ActionRegistry,
        runner: ActionRunner,
        publisher: ResponsePublisherProtocol,
        localizer: Localizer | None = None,
    ) -> None:
        self._gateway = gateway
        self._registry = registry
        self._runner = runner
        self._publisher = publisher
        self._localizer = localizer or Localizer()

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

        await update.effective_chat.send_action("typing")

        session = UserSession.from_context(context)
        language_pair = session.language_pair

        try:
            anchor = await self._gateway.process(update, language_pair)
        except UserFacingError as exc:
            await update.message.reply_text(
                self._localizer.t(type(exc), session.base_language, **exc.format_kwargs)
            )
            return

        action_type = ActionType.TRANSLATE
        action = self._registry.get(action_type)

        result = await self._runner.run(
            action, anchor, language_pair, user_id=update.effective_user.id
        )

        msg_id = await self._publisher.publish_new_slot(
            result=result,
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.message.message_id,
            session=session,
            reply_markup=KEYBOARD,
            user_id=update.effective_user.id,
        )
        if result.run_id:
            session.store_run_id(msg_id, result.run_id)
