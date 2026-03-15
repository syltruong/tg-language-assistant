"""Shared factory functions for building fake Telegram Update and Context objects."""

from unittest.mock import AsyncMock, MagicMock

from telegram import CallbackQuery, Chat, Message, Update, User


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
    update.callback_query = None

    return update


def make_callback_update(
    callback_data: str,
    user_id: int = 123,
    chat_id: int = 456,
    message_id: int = 789,
) -> MagicMock:
    """Factory for fake Update with a callback_query (inline button click)."""
    user = MagicMock(spec=User)
    user.id = user_id
    user.is_bot = False

    chat = MagicMock(spec=Chat)
    chat.id = chat_id

    message = MagicMock(spec=Message)
    message.message_id = message_id
    message.chat = chat

    query = MagicMock(spec=CallbackQuery)
    query.data = callback_data
    query.message = message
    query.answer = AsyncMock()
    query.edit_message_reply_markup = AsyncMock()

    update = MagicMock(spec=Update)
    update.callback_query = query
    update.effective_user = user
    update.effective_chat = chat
    update.message = None

    return update


def make_context(user_data: dict | None = None) -> MagicMock:
    """Factory for fake Context objects."""
    from telegram.ext import ContextTypes

    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.bot.edit_message_text = AsyncMock()
    context.user_data = user_data if user_data is not None else {}
    return context
