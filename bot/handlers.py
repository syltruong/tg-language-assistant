"""Telegram handler functions for the language-assistant bot.

Every handler receives a ``context`` (``CallbackContext``) that the
python-telegram-bot framework creates and passes automatically.  It exposes
scoped state dicts that persist for the lifetime of the bot process:

- ``context.user_data``  -- dict unique to each Telegram user.
- ``context.chat_data``  -- dict scoped per chat (relevant in group chats).
- ``context.bot_data``   -- global dict shared across all users and chats.
- ``context.bot``        -- reference to the ``Bot`` instance itself.

The framework routes the correct dict to each handler call, so
``context.user_data`` in one user's handler is isolated from another's.

All of this is **in-memory only** by default; a process restart loses the
data.  To make it durable, plug in a persistence backend:
https://docs.python-telegram-bot.org/en/stable/telegram.ext.persistenceclass.html
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import STREAMING_ENABLED, STREAM_CHUNK_SIZE, ALLOWED_USERS
from bot.prompts import SYSTEM_PROMPT, PROMPTS
from bot.keyboard import make_keyboard
from bot.llm import get_completion, stream_completion
from bot.strings import (
    MSG_TOO_LONG,
    MSG_CHOOSE_ACTION,
    MSG_CLEAR,
    MSG_UNKNOWN_ACTION,
    MSG_NO_MESSAGE,
    MSG_THINKING,
    MSG_NO_CONTENT,
    MSG_AI_ERROR,
    MSG_UNAUTHORIZED,
)

logger = logging.getLogger(__name__)


def _is_authorized(user_id: int | None) -> bool:
    """Return True if the user is allowed to use the bot."""
    if not ALLOWED_USERS:
        return True
    return user_id in ALLOWED_USERS


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages from users. Deflect if message is too long. Else, ask user to choose an action."""
    user_id = update.effective_user.id if update.effective_user else None
    if not _is_authorized(user_id):
        logger.warning("Unauthorized access attempt by user=%s", user_id)
        await update.message.reply_text(MSG_UNAUTHORIZED)
        return

    if len(update.message.text) > 100:
        await update.message.reply_text(
            MSG_TOO_LONG,
            reply_to_message_id=update.message.message_id,
        )
        return

    reply = await update.message.reply_text(
        text=MSG_CHOOSE_ACTION,
        reply_markup=make_keyboard(),
        reply_to_message_id=update.message.message_id,
    )
    # Key the original text by the reply's message ID so each keyboard
    # resolves to the message it was triggered from
    context.user_data.setdefault("messages", {})[reply.message_id] = update.message.text


async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline-keyboard button clicks."""
    user_id = update.effective_user.id if update.effective_user else None
    if not _is_authorized(user_id):
        logger.warning("Unauthorized button click by user=%s", user_id)
        await update.callback_query.answer(text=MSG_UNAUTHORIZED, show_alert=True)
        return

    query = update.callback_query
    await query.answer()

    callback_data = query.data

    if callback_data == "clear":
        await query.answer(text="Dismissed!", show_alert=True)
        await query.edit_message_reply_markup(reply_markup=None) # TODO: change to a one-button keyboard to open back the menu
        return

    if callback_data not in PROMPTS:
        await query.answer(text=MSG_UNKNOWN_ACTION, show_alert=True)
        return

    original_text = context.user_data.get("messages", {}).get(query.message.message_id, "")
    if not original_text:
        await query.edit_message_text(text=MSG_NO_MESSAGE)
        return

    await query.edit_message_text(text=MSG_THINKING)

    prompt = PROMPTS[callback_data] + "\n" + original_text

    try:
        if STREAMING_ENABLED:
            await _stream_response(query, prompt)
        else:
            await _send_response(query, prompt)
    except Exception as e:
        logging.error("OpenAI API error: %s", e)
        await query.edit_message_text(text=MSG_AI_ERROR.format(error=e))


async def _stream_response(query, prompt: str) -> None:
    """Stream an LLM response, progressively editing the Telegram message."""
    user_id = getattr(query.from_user, "id", None)

    try:
        logging.info("Starting streaming for user=%s", user_id)

        accumulated = ""
        last_sent_len = 0
        await query.edit_message_text(text="", reply_markup=None)

        async for chunk in stream_completion(prompt, SYSTEM_PROMPT):
            logging.debug("Received chunk size=%d for user=%s", len(chunk), user_id)
            accumulated += chunk
            if len(accumulated) - last_sent_len >= STREAM_CHUNK_SIZE:
                await query.edit_message_text(text=accumulated)
                last_sent_len = len(accumulated)
                logging.info("Sent edit update (%d chars) for user=%s", last_sent_len, user_id)

        await query.edit_message_text(
            text=accumulated or MSG_NO_CONTENT,
            reply_markup=make_keyboard(),
        )
        logging.info("Streaming finished for user=%s total_chars=%d", user_id, len(accumulated))

    except Exception as e:
        logging.warning("Streaming failed, falling back to non-streaming: %s", e)
        await _send_response(query, prompt)


async def _send_response(query, prompt: str) -> None:
    """Send a single non-streaming LLM response."""
    llm_reply = await get_completion(prompt, SYSTEM_PROMPT)
    await query.edit_message_text(text=llm_reply, reply_markup=make_keyboard())
