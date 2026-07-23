"""ResponsePublisher — delivers a formatted result to the user via Telegram."""

import asyncio
from typing import Protocol, runtime_checkable

from telegram import Bot, InlineKeyboardMarkup

from bot.session import UserSession
from bot.types import FormattedResult


@runtime_checkable
class ResponsePublisherProtocol(Protocol):
    async def publish_new_slot(
        self,
        result: FormattedResult,
        chat_id: int,
        reply_to_message_id: int,
        session: UserSession,
        reply_markup: InlineKeyboardMarkup | None = None,
        user_id: int = 0,
    ) -> int: ...

    async def edit_slot(
        self,
        result: FormattedResult,
        chat_id: int,
        slot_id: int,
        session: UserSession,
        reply_markup: InlineKeyboardMarkup | None = None,
        user_id: int = 0,
    ) -> None: ...


class FakeResponsePublisher:
    def __init__(self, next_message_id: int = 1000) -> None:
        self.new_slots_published: list[tuple[FormattedResult, int, int, InlineKeyboardMarkup | None]] = []
        self.edits: list[tuple[FormattedResult, int, int, InlineKeyboardMarkup | None]] = []
        self._next_message_id = next_message_id

    async def publish_new_slot(
        self,
        result: FormattedResult,
        chat_id: int,
        reply_to_message_id: int,
        session: UserSession,
        reply_markup: InlineKeyboardMarkup | None = None,
        user_id: int = 0,
    ) -> int:
        self.new_slots_published.append((result, chat_id, reply_to_message_id, reply_markup))
        msg_id = self._next_message_id
        self._next_message_id += 1
        return msg_id

    async def edit_slot(
        self,
        result: FormattedResult,
        chat_id: int,
        slot_id: int,
        session: UserSession,
        reply_markup: InlineKeyboardMarkup | None = None,
        user_id: int = 0,
    ) -> None:
        self.edits.append((result, chat_id, slot_id, reply_markup))


class ResponsePublisher:
    def __init__(self, bot: Bot) -> None:
        self._bot = bot
        self._locks: dict[int, asyncio.Lock] = {}

    def _get_lock(self, user_id: int) -> asyncio.Lock:
        if user_id not in self._locks:
            self._locks[user_id] = asyncio.Lock()
        return self._locks[user_id]

    async def publish_new_slot(
        self,
        result: FormattedResult,
        chat_id: int,
        reply_to_message_id: int,
        session: UserSession,
        reply_markup: InlineKeyboardMarkup | None = None,
        user_id: int = 0,
    ) -> int:
        async with self._get_lock(user_id):
            active = session.get_active_slot_id()
            if active is not None:
                await self._bot.edit_message_reply_markup(chat_id=chat_id, message_id=active, reply_markup=None)
            msg = await self._bot.send_message(
                chat_id=chat_id,
                text=result.text,
                parse_mode=result.parse_mode,
                reply_to_message_id=reply_to_message_id,
                reply_markup=reply_markup,
            )
            session.set_active_slot_id(msg.message_id)
            return msg.message_id

    async def edit_slot(
        self,
        result: FormattedResult,
        chat_id: int,
        slot_id: int,
        session: UserSession,
        reply_markup: InlineKeyboardMarkup | None = None,
        user_id: int = 0,
    ) -> None:
        async with self._get_lock(user_id):
            active = session.get_active_slot_id()
            if active is not None and active != slot_id:
                await self._bot.edit_message_reply_markup(chat_id=chat_id, message_id=active, reply_markup=None)
            await self._bot.edit_message_text(
                chat_id=chat_id,
                message_id=slot_id,
                text=result.text,
                parse_mode=result.parse_mode,
                reply_markup=reply_markup,
            )
            session.set_active_slot_id(slot_id)
