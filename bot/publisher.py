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
        if session.active_keyboard_id is not None:
            await self._bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=session.active_keyboard_id,
                reply_markup=None,
            )

        msg = await self._bot.send_message(
            chat_id=chat_id,
            text=result.text,
            parse_mode=result.parse_mode,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
        )
        session.active_keyboard_id = msg.message_id

