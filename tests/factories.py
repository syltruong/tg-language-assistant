"""Shared factory functions for building fake Telegram Update and Context objects."""

from unittest.mock import AsyncMock, MagicMock

from telegram import Chat, Message, Update, User


def make_update(
    text: str | None = "Hello",
    user_id: int = 123,
    chat_id: int = 456,
) -> MagicMock:
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
