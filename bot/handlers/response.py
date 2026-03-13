import logging
from collections.abc import AsyncIterator

from telegram import InlineKeyboardMarkup

from bot.config import STREAM_CHUNK_SIZE
from bot.config.messages import MsgNoContent, t


async def _stream_response(
    query, stream: AsyncIterator[str], reply_markup: InlineKeyboardMarkup,
) -> None:
    """Consume a streaming LLM response, progressively editing the Telegram message.

    ``stream`` delivers the LLM's output one small string chunk at a time,
    as tokens arrive over the network — rather than waiting for the full
    response before doing anything.

    ``async for chunk in stream`` works like a normal for-loop, except between
    each iteration it waits for the next chunk to arrive over the network.
    During that wait the rest of the bot keeps running — other users' requests
    are not blocked.

    As chunks arrive they are appended to ``accumulated``.  Every
    ``STREAM_CHUNK_SIZE`` characters the Telegram message is edited in-place,
    giving the user a live "typing" effect.  A final edit restores the action
    keyboard once the stream is exhausted.
    """
    user_id = getattr(query.from_user, "id", None)
    logging.info("Starting streaming for user=%s", user_id)

    accumulated = ""
    last_sent_len = 0

    async for chunk in stream:
        logging.debug("Received chunk size=%d for user=%s", len(chunk), user_id)
        accumulated += chunk
        if len(accumulated) - last_sent_len >= STREAM_CHUNK_SIZE:
            await query.edit_message_text(text=accumulated)
            last_sent_len = len(accumulated)
            logging.info(
                "Sent edit update (%d chars) for user=%s",
                last_sent_len, user_id,
            )

    await query.edit_message_text(
        text=accumulated or t(MsgNoContent),
        reply_markup=reply_markup,
    )
    logging.info(
        "Streaming finished for user=%s total_chars=%d",
        user_id, len(accumulated),
    )


async def _send_response(query, text: str, reply_markup: InlineKeyboardMarkup) -> None:
    """Edit the Telegram message with a completed LLM response."""
    await query.edit_message_text(text=text, reply_markup=reply_markup)
