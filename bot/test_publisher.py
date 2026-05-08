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


class TestResponsePublisherKeyboardLifecycle:
    @pytest.mark.asyncio
    async def test_first_publish_sends_new_message(self):
        bot = _make_bot(sent_message_id=42)
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)

        await publisher.publish(FormattedResult("Hi", None), chat_id=1, reply_to_message_id=2, session=session)

        bot.send_message.assert_called_once()
        bot.edit_message_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_second_publish_edits_in_place(self):
        bot = _make_bot(sent_message_id=77)
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)
        await publisher.publish(FormattedResult("First", None), chat_id=1, reply_to_message_id=2, session=session)
        bot.send_message.reset_mock()

        await publisher.publish(FormattedResult("Updated", None), chat_id=1, reply_to_message_id=2, session=session)

        bot.edit_message_text.assert_called_once()
        bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_edit_in_place_uses_slot_message_id(self):
        bot = _make_bot(sent_message_id=77)
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)
        await publisher.publish(FormattedResult("First", None), chat_id=5, reply_to_message_id=2, session=session)
        bot.edit_message_text.reset_mock()

        await publisher.publish(
            FormattedResult("New text", None),
            chat_id=5,
            reply_to_message_id=2,
            session=session,
            reply_markup=None,
        )

        call_kwargs = bot.edit_message_text.call_args.kwargs
        assert call_kwargs["chat_id"] == 5
        assert call_kwargs["message_id"] == 77
        assert call_kwargs["text"] == "New text"


    @pytest.mark.asyncio
    async def test_second_publish_for_different_anchor_sends_new_message(self):
        bot = _make_bot(sent_message_id=99)
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)

        # First publish for anchor 10 — establishes a keyboard slot
        await publisher.publish(FormattedResult("First", None), chat_id=1, reply_to_message_id=10, session=session)
        bot.send_message.reset_mock()
        bot.edit_message_text.reset_mock()

        # Second publish for a different anchor 20 — must send fresh, not edit
        await publisher.publish(FormattedResult("Second", None), chat_id=1, reply_to_message_id=20, session=session)

        bot.send_message.assert_called_once()
        bot.edit_message_text.assert_not_called()


class TestResponsePublisherReplyMarkup:
    @pytest.mark.asyncio
    async def test_forwards_reply_markup_to_send_message(self):
        from bot.keyboard import KEYBOARD

        bot = _make_bot(sent_message_id=42)
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)

        await publisher.publish(
            FormattedResult("Hi", None),
            chat_id=1,
            reply_to_message_id=2,
            session=session,
            reply_markup=KEYBOARD,
        )

        call_kwargs = bot.send_message.call_args.kwargs
        assert call_kwargs["reply_markup"] is KEYBOARD

    @pytest.mark.asyncio
    async def test_sends_without_markup_by_default(self):
        bot = _make_bot(sent_message_id=42)
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)

        await publisher.publish(FormattedResult("Hi", None), chat_id=1, reply_to_message_id=2, session=session)

        call_kwargs = bot.send_message.call_args.kwargs
        assert call_kwargs.get("reply_markup") is None


class TestResponsePublisherParseMode:
    @pytest.mark.asyncio
    async def test_forwards_html_parse_mode_to_send_message(self):
        bot = _make_bot()
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)

        await publisher.publish(
            FormattedResult("<b>Bonjour</b>", "HTML"),
            chat_id=1,
            reply_to_message_id=2,
            session=session,
        )

        call_kwargs = bot.send_message.call_args.kwargs
        assert call_kwargs["parse_mode"] == "HTML"

    @pytest.mark.asyncio
    async def test_forwards_none_parse_mode_to_send_message(self):
        bot = _make_bot()
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)

        await publisher.publish(
            FormattedResult("Bonjour", None),
            chat_id=1,
            reply_to_message_id=2,
            session=session,
        )

        call_kwargs = bot.send_message.call_args.kwargs
        assert call_kwargs["parse_mode"] is None


class TestResponsePublisherSendsResult:
    @pytest.mark.asyncio
    async def test_sends_result_to_correct_chat(self):
        bot = _make_bot(sent_message_id=42)
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)

        await publisher.publish(
            FormattedResult("Hello!", None), chat_id=1, reply_to_message_id=2, session=session
        )

        bot.send_message.assert_called_once()
        call_kwargs = bot.send_message.call_args
        assert call_kwargs.kwargs["chat_id"] == 1
        assert call_kwargs.kwargs["text"] == "Hello!"

    @pytest.mark.asyncio
    async def test_stores_keyboard_id_for_anchor_after_sending(self):
        bot = _make_bot(sent_message_id=42)
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)

        await publisher.publish(
            FormattedResult("Hello!", None), chat_id=1, reply_to_message_id=2, session=session
        )

        assert session.get_keyboard_id(2) == 42
