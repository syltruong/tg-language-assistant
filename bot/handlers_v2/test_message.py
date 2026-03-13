"""Unit tests for the message handler."""
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Chat, Message, Update, User

from bot.config.messages import t
from bot.handlers_v2.message import handle_message
from bot.routing.local import (
    MessageHasNoTextException,
    TextHasNoWrittenContentException,
    TextTooLongException,
)


def make_update(text: str = "Hello", user_id: int = 123, chat_id: int = 456) -> MagicMock:
    """Factory for fake Update objects."""
    user = MagicMock(spec=User)
    user.id = user_id
    user.is_bot = False

    chat = MagicMock(spec=Chat)
    chat.id = chat_id
    chat.send_action = AsyncMock()

    message = MagicMock(spec=Message)
    message.text = text
    message.from_user = user
    message.chat = chat
    message.reply_text = AsyncMock()

    update = MagicMock(spec=Update)
    update.message = message
    update.effective_user = user
    update.effective_chat = chat

    return update


def make_context() -> MagicMock:
    """Factory for fake Context objects."""
    from telegram.ext import ContextTypes

    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    return context


# ── Happy path ───────────────────────────────────────────────────────


@patch("bot.handlers_v2.message.detect_language", return_value="fr")
@patch("bot.handlers_v2.message.filter_telegram_text_message")
class TestHandleMessageHappyPath:
    async def test_sends_typing_action(self, _mock_filter, _mock_detect):
        update = make_update("Bonjour")
        await handle_message(update, make_context())

        update.effective_chat.send_action.assert_called_once_with("typing")

    async def test_calls_filter_with_message(self, mock_filter, _mock_detect):
        update = make_update("Bonjour")
        await handle_message(update, make_context())

        mock_filter.assert_called_once_with(update.message)

    async def test_calls_detect_language(self, _mock_filter, mock_detect):
        update = make_update("Bonjour")
        await handle_message(update, make_context())

        mock_detect.assert_called_once()


# ── UserFacingError paths ────────────────────────────────────────────


class TestHandleMessageErrors:
    @patch(
        "bot.handlers_v2.message.filter_telegram_text_message",
        side_effect=TextTooLongException(),
    )
    async def test_too_long_replies_with_error(self, _mock_filter):
        update = make_update("a" * 501)
        await handle_message(update, make_context())

        update.message.reply_text.assert_called_once_with(t(TextTooLongException))

    @patch(
        "bot.handlers_v2.message.filter_telegram_text_message",
        side_effect=MessageHasNoTextException(),
    )
    async def test_no_text_replies_with_error(self, _mock_filter):
        update = make_update("")
        await handle_message(update, make_context())

        update.message.reply_text.assert_called_once_with(t(MessageHasNoTextException))

    @patch(
        "bot.handlers_v2.message.filter_telegram_text_message",
        side_effect=TextHasNoWrittenContentException(),
    )
    async def test_no_written_content_replies_with_error(self, _mock_filter):
        update = make_update("!!!")
        await handle_message(update, make_context())

        update.message.reply_text.assert_called_once_with(
            t(TextHasNoWrittenContentException),
        )

    @patch(
        "bot.handlers_v2.message.filter_telegram_text_message",
        side_effect=TextTooLongException(),
    )
    async def test_error_still_sends_typing(self, _mock_filter):
        update = make_update("a" * 501)
        await handle_message(update, make_context())

        update.effective_chat.send_action.assert_called_once_with("typing")

    @patch(
        "bot.handlers_v2.message.filter_telegram_text_message",
        side_effect=TextTooLongException(),
    )
    @patch("bot.handlers_v2.message.detect_language")
    async def test_error_skips_detect_language(self, mock_detect, _mock_filter):
        update = make_update("a" * 501)
        await handle_message(update, make_context())

        mock_detect.assert_not_called()
