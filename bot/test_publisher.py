import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import Bot, Message

from bot.publisher import ResponsePublisher
from bot.session import UserSession
from bot.types import FormattedResult


def _make_bot(sent_message_id: int = 42) -> MagicMock:
    msg = MagicMock(spec=Message)
    msg.message_id = sent_message_id

    bot = MagicMock(spec=Bot)
    bot.send_message = AsyncMock(return_value=msg)
    bot.edit_message_reply_markup = AsyncMock()
    bot.edit_message_text = AsyncMock()
    return bot


class TestPublishNewSlot:
    @pytest.mark.asyncio
    async def test_sends_message_replying_to_anchor(self):
        bot = _make_bot(sent_message_id=42)
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)

        await publisher.publish_new_slot(FormattedResult("Hi", None), chat_id=1, reply_to_message_id=2, session=session, user_id=1)

        bot.send_message.assert_called_once()
        assert bot.send_message.call_args.kwargs["reply_to_message_id"] == 2
        bot.edit_message_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_sets_new_slot_as_active(self):
        bot = _make_bot(sent_message_id=42)
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)

        await publisher.publish_new_slot(FormattedResult("Hi", None), chat_id=1, reply_to_message_id=2, session=session, user_id=1)

        assert session.get_active_slot_id() == 42

    @pytest.mark.asyncio
    async def test_deactivates_previous_active_slot(self):
        bot = _make_bot(sent_message_id=99)
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)

        await publisher.publish_new_slot(FormattedResult("First", None), chat_id=1, reply_to_message_id=10, session=session, user_id=1)
        bot.edit_message_reply_markup.reset_mock()

        await publisher.publish_new_slot(FormattedResult("Second", None), chat_id=1, reply_to_message_id=20, session=session, user_id=1)

        bot.edit_message_reply_markup.assert_called_once_with(chat_id=1, message_id=99, reply_markup=None)

    @pytest.mark.asyncio
    async def test_forwards_reply_markup(self):
        from bot.keyboard import KEYBOARD
        bot = _make_bot(sent_message_id=42)
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)

        await publisher.publish_new_slot(FormattedResult("Hi", None), chat_id=1, reply_to_message_id=2, session=session, reply_markup=KEYBOARD, user_id=1)

        assert bot.send_message.call_args.kwargs["reply_markup"] is KEYBOARD

    @pytest.mark.asyncio
    async def test_forwards_parse_mode(self):
        bot = _make_bot()
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)

        await publisher.publish_new_slot(FormattedResult("<b>Hi</b>", "HTML"), chat_id=1, reply_to_message_id=2, session=session, user_id=1)

        assert bot.send_message.call_args.kwargs["parse_mode"] == "HTML"

    @pytest.mark.asyncio
    async def test_concurrent_calls_for_same_user_are_serialised(self):
        call_order: list[str] = []

        msg = MagicMock(spec=Message)
        msg.message_id = 42
        bot = MagicMock(spec=Bot)
        bot.edit_message_reply_markup = AsyncMock()
        bot.edit_message_text = AsyncMock()

        async def slow_send(**kwargs):
            call_order.append("start")
            await asyncio.sleep(0.05)
            call_order.append("end")
            return msg

        bot.send_message = AsyncMock(side_effect=slow_send)
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)

        await asyncio.gather(
            publisher.publish_new_slot(FormattedResult("A", None), chat_id=1, reply_to_message_id=10, session=session, user_id=1),
            publisher.publish_new_slot(FormattedResult("B", None), chat_id=1, reply_to_message_id=20, session=session, user_id=1),
        )

        assert call_order == ["start", "end", "start", "end"]


class TestEditSlot:
    @pytest.mark.asyncio
    async def test_edits_slot_message_with_given_slot_id(self):
        bot = _make_bot()
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)

        await publisher.edit_slot(FormattedResult("Updated", None), chat_id=5, slot_id=77, session=session, user_id=1)

        bot.edit_message_text.assert_called_once()
        assert bot.edit_message_text.call_args.kwargs["message_id"] == 77
        assert bot.edit_message_text.call_args.kwargs["chat_id"] == 5
        bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_sets_slot_as_active(self):
        bot = _make_bot()
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)

        await publisher.edit_slot(FormattedResult("Hi", None), chat_id=1, slot_id=77, session=session, user_id=1)

        assert session.get_active_slot_id() == 77

    @pytest.mark.asyncio
    async def test_skips_deactivation_when_editing_active_slot(self):
        bot = _make_bot(sent_message_id=77)
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)
        await publisher.publish_new_slot(FormattedResult("First", None), chat_id=1, reply_to_message_id=10, session=session, user_id=1)
        bot.edit_message_reply_markup.reset_mock()

        await publisher.edit_slot(FormattedResult("Updated", None), chat_id=1, slot_id=77, session=session, user_id=1)

        bot.edit_message_reply_markup.assert_not_called()

    @pytest.mark.asyncio
    async def test_deactivates_previous_slot_when_editing_non_active(self):
        bot = _make_bot(sent_message_id=100)
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)
        await publisher.publish_new_slot(FormattedResult("A", None), chat_id=1, reply_to_message_id=10, session=session, user_id=1)
        bot.edit_message_reply_markup.reset_mock()

        await publisher.edit_slot(FormattedResult("B", None), chat_id=1, slot_id=55, session=session, user_id=1)

        bot.edit_message_reply_markup.assert_called_once_with(chat_id=1, message_id=100, reply_markup=None)

    @pytest.mark.asyncio
    async def test_forwards_reply_markup(self):
        from bot.keyboard import KEYBOARD
        bot = _make_bot()
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)

        await publisher.edit_slot(FormattedResult("Hi", None), chat_id=1, slot_id=77, session=session, reply_markup=KEYBOARD, user_id=1)

        assert bot.edit_message_text.call_args.kwargs["reply_markup"] is KEYBOARD

    @pytest.mark.asyncio
    async def test_forwards_parse_mode(self):
        bot = _make_bot()
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)

        await publisher.edit_slot(FormattedResult("<b>Hi</b>", "HTML"), chat_id=1, slot_id=77, session=session, user_id=1)

        assert bot.edit_message_text.call_args.kwargs["parse_mode"] == "HTML"
