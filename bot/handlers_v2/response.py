from collections.abc import AsyncIterator

from telegram import Bot, InlineKeyboardMarkup, Message

from bot.config import STREAM_CHUNK_SIZE
from bot.config.messages import MsgNoContent, t


async def stream_response(
    bot: Bot,
    chat_id: int,
    stream: AsyncIterator[str],
    *,
    reply_to_message_id: int | None = None,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    """Send a new message that streams in, replying to an existing message.

    Use when there is no message to edit (e.g. user sent a text message).
    Sends an initial message (reply_to_message_id sets which message it replies to),
    then edits that new message as chunks arrive.
    """
    placeholder = "…"
    msg = await bot.send_message(
        chat_id=chat_id,
        text=placeholder,
        reply_to_message_id=reply_to_message_id,
    )
    message_id = msg.message_id

    accumulated = ""
    last_sent_len = 0

    async for chunk in stream:
        accumulated += chunk
        if len(accumulated) - last_sent_len >= STREAM_CHUNK_SIZE:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=accumulated,
            )
            last_sent_len = len(accumulated)

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=accumulated or t(MsgNoContent), # TODO: handle case where LLM returns no content (e.g. due to moderation filter) more gracefully
        reply_markup=reply_markup,
    )


async def send_response(
    bot: Bot,
    chat_id: int,
    text: str,
    *,
    reply_to_message_id: int | None = None,
    reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode: str | None = None,
) -> Message:
    """Send a new message with the LLM response, replying to an existing message."""
    msg = await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_to_message_id=reply_to_message_id,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
    )
    return msg
