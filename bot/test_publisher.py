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
    return bot


class TestResponsePublisherKeyboardLifecycle:
    @pytest.mark.asyncio
    async def test_removes_old_keyboard_before_sending(self):
        bot = _make_bot(sent_message_id=99)
        session = UserSession({"active_keyboard_id": 77})
        publisher = ResponsePublisher(bot=bot)

        call_order = []
        bot.edit_message_reply_markup.side_effect = lambda **kw: call_order.append(
            "remove"
        )
        bot.send_message.side_effect = lambda **kw: (
            call_order.append("send") or bot.send_message.return_value
        )

        await publisher.publish(FormattedResult("Hi", None), chat_id=1, reply_to_message_id=2, session=session)

        bot.edit_message_reply_markup.assert_called_once_with(
            chat_id=1, message_id=77, reply_markup=None
        )
        assert call_order == ["remove", "send"]

    @pytest.mark.asyncio
    async def test_skips_keyboard_removal_when_no_active_keyboard(self):
        bot = _make_bot()
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)

        await publisher.publish(FormattedResult("Hi", None), chat_id=1, reply_to_message_id=2, session=session)

        bot.edit_message_reply_markup.assert_not_called()


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


class TestResponsePublisherReattachKeyboard:
    @pytest.mark.asyncio
    async def test_reattach_calls_edit_with_markup(self):
        from bot.keyboard import KEYBOARD

        bot = _make_bot()
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)

        await publisher.reattach_keyboard(
            chat_id=1, message_id=77, reply_markup=KEYBOARD, session=session
        )

        bot.edit_message_reply_markup.assert_called_once_with(
            chat_id=1, message_id=77, reply_markup=KEYBOARD
        )

    @pytest.mark.asyncio
    async def test_reattach_updates_active_keyboard_id(self):
        from bot.keyboard import KEYBOARD

        bot = _make_bot()
        session = UserSession({"active_keyboard_id": 99})
        publisher = ResponsePublisher(bot=bot)

        await publisher.reattach_keyboard(
            chat_id=1, message_id=77, reply_markup=KEYBOARD, session=session
        )

        assert session.active_keyboard_id == 77


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
    async def test_sets_active_keyboard_id_after_sending(self):
        bot = _make_bot(sent_message_id=42)
        session = UserSession({})
        publisher = ResponsePublisher(bot=bot)

        await publisher.publish(
            FormattedResult("Hello!", None), chat_id=1, reply_to_message_id=2, session=session
        )

        assert session.active_keyboard_id == 42
