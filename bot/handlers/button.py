import json
import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import N_SUGGESTED_REPLIES, STREAMING_ENABLED
from bot.config.strings import (
    MSG_AI_ERROR,
    MSG_CHOOSE_ACTION,
    MSG_CLEAR,
    MSG_NO_MESSAGE,
    MSG_THINKING,
    MSG_UNAUTHORIZED,
    MSG_UNKNOWN_ACTION,
)
from bot.handlers.auth import _is_authorized
from bot.handlers.response import _send_response, _stream_response
from bot.keyboard import NUMBER_EMOJIS, make_keyboard, make_reply_keyboard
from bot.llm import get_completion, stream_completion
from bot.prompts import PROMPTS, SYSTEM_PROMPT
from bot.session import UserSession
from bot.types import ActionType, ReplySuggestion

logger = logging.getLogger(__name__)


async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline-keyboard button clicks."""
    user_id = update.effective_user.id if update.effective_user else None
    if not _is_authorized(user_id):
        logger.warning("Unauthorized button click by user=%s", user_id)
        # This line sends an alert popup to the user via Telegram when they press a button they aren't authorized to use.
        await update.callback_query.answer(text=MSG_UNAUTHORIZED, show_alert=True)
        return

    # await update.effective_chat.send_action("typing")
    query = update.callback_query
    await query.answer()
    bot_message_id = query.message.message_id
    callback_data = query.data

    if callback_data == "clear":
        await query.edit_message_text(text=MSG_CLEAR, reply_markup=None)
        return

    session = UserSession.from_context(context)

    if callback_data == "back":
        await query.edit_message_text(
            text=MSG_CHOOSE_ACTION,
            reply_markup=make_keyboard(session.get_action_types(bot_message_id)),
        )
        return

    if callback_data.startswith("reply_"):
        idx = int(callback_data.removeprefix("reply_"))
        replies = session.get_replies(bot_message_id)
        if idx < len(replies):
            await query.edit_message_text(text=replies[idx].reply)
        else:
            await query.edit_message_text(text=MSG_NO_MESSAGE)
        return

    if callback_data not in PROMPTS:
        await query.answer(text=MSG_UNKNOWN_ACTION, show_alert=True)
        return

    original_text = session.get_message(bot_message_id)
    if not original_text:
        await query.edit_message_text(text=MSG_NO_MESSAGE)
        return

    await query.edit_message_text(text=MSG_THINKING)

    if callback_data == ActionType.REPLY:
        await _handle_reply(query, session, original_text)
        return

    action_types = session.get_action_types(bot_message_id)
    await _handle_non_reply_action(query, callback_data, original_text, action_types)


async def _handle_non_reply_action(query, action_type: ActionType, original_text: str, action_types) -> None:
    """Run an LLM completion for a non-reply action and update the message."""
    prompt = f"{PROMPTS[action_type]}\n<text>\n{original_text}\n</text>"
    reply_markup = make_keyboard(action_types)

    try:
        if STREAMING_ENABLED:
            try:
                stream = stream_completion(SYSTEM_PROMPT, prompt)
                await _stream_response(query, stream, reply_markup)
            except Exception as e:
                logging.warning("Streaming failed, falling back to non-streaming: %s", e)
                text = await get_completion(SYSTEM_PROMPT, prompt)
                await _send_response(query, text, reply_markup)
        else:
            text = await get_completion(SYSTEM_PROMPT, prompt)
            await _send_response(query, text, reply_markup)
    except Exception as e:
        logging.error("OpenAI API error: %s", e)
        await query.edit_message_text(text=MSG_AI_ERROR.format(error=e))


async def _handle_reply(query, session: UserSession, original_text: str) -> None:
    """Generate suggested replies and present them as numbered buttons."""

    prompt_template = PROMPTS[ActionType.REPLY]
    prompt = prompt_template.format(n=N_SUGGESTED_REPLIES)
    prompt = f"{prompt}\n<text>\n{original_text}\n</text>"

    try:
        raw = await get_completion(SYSTEM_PROMPT, prompt)
        logging.info("Raw response: %s", raw)
        replies = [ReplySuggestion(**r) for r in json.loads(raw)]
    except (json.JSONDecodeError, Exception) as e:
        logging.error("Failed to parse reply suggestions: %s", e)
        logging.error("Raw response: %s", raw)
        await query.edit_message_text(text=MSG_AI_ERROR.format(error=e))
        return

    session.store_replies(query.message.message_id, replies)

    lines = [
        f"{NUMBER_EMOJIS[i]}  {r.reply}  ({r.tone})"
        for i, r in enumerate(replies)
    ]
    body = "\n\n".join(lines)

    await query.edit_message_text(
        text=body,
        reply_markup=make_reply_keyboard(len(replies)),
    )
