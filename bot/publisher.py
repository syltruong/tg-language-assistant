"""ResponsePublisher — delivers a formatted result to the user via Telegram."""

from telegram import Bot, InlineKeyboardMarkup

from bot.session import UserSession
from bot.types import FormattedResult


class FakeResponsePublisher:
    def __init__(self) -> None:
        self.published: list[tuple[FormattedResult, int, int, InlineKeyboardMarkup | None]] = []

    async def publish(
        self,
        result: FormattedResult,
        chat_id: int,
        reply_to_message_id: int,
        session: UserSession,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> None:
        self.published.append((result, chat_id, reply_to_message_id, reply_markup))

class ResponsePublisher:
    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def publish(
        self,
        result: FormattedResult,
        chat_id: int,
        reply_to_message_id: int,
        session: UserSession,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> None:
        await self._deactivate_previous_slot(chat_id, reply_to_message_id, session)

        slot_id = session.get_slot_id(reply_to_message_id)
        if slot_id is not None:
            await self._bot.edit_message_text(
                chat_id=chat_id,
                message_id=slot_id,
                text=result.text,
                parse_mode=result.parse_mode,
                reply_markup=reply_markup,
            )
        else:
            msg = await self._bot.send_message(
                chat_id=chat_id,
                text=result.text,
                parse_mode=result.parse_mode,
                reply_to_message_id=reply_to_message_id,
                reply_markup=reply_markup,
            )
            slot_id = msg.message_id
            session.set_slot_id(reply_to_message_id, slot_id)

        session.set_active_slot_id(slot_id)

    async def _deactivate_previous_slot(
        self, chat_id: int, reply_to_message_id: int, session: UserSession
    ) -> None:
        active_slot_id = session.get_active_slot_id()
        if active_slot_id is None:
            return
        if session.get_slot_id(reply_to_message_id) == active_slot_id:
            return
        await self._bot.edit_message_reply_markup(
            chat_id=chat_id, message_id=active_slot_id, reply_markup=None
        )

