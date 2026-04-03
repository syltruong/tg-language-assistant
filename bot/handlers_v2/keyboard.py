import json

from loguru import logger
from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.config import N_SUGGESTED_REPLIES
from bot.config.messages import MsgNoReplyText, t
from bot.handlers_v2.response import send_response
from bot.llm import get_completion
from bot.prompts_v2 import KEYBOARD_PROMPTS, SYSTEM_PROMPT
from bot.session import UserSession
from bot.types import KeyboardActionType

# TODO: localise the button titles
BUTTON_TITLES: dict[KeyboardActionType, str] = {
    KeyboardActionType.ANALYZE: "📖 Analyze",
    KeyboardActionType.CORRECT: "✏️ Correct",
    KeyboardActionType.REPHRASE: "🧠 Rephrase",
    KeyboardActionType.REPLY: "💬 Reply",
}

BUTTON_ACTIONS = list(BUTTON_TITLES.keys())

KEYBOARD = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(BUTTON_TITLES[KeyboardActionType.ANALYZE], callback_data=KeyboardActionType.ANALYZE),
            InlineKeyboardButton(BUTTON_TITLES[KeyboardActionType.CORRECT], callback_data=KeyboardActionType.CORRECT),
        ],
        [
            InlineKeyboardButton(BUTTON_TITLES[KeyboardActionType.REPHRASE], callback_data=KeyboardActionType.REPHRASE),
            InlineKeyboardButton(BUTTON_TITLES[KeyboardActionType.REPLY], callback_data=KeyboardActionType.REPLY),
        ],
    ]
)


async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline-keyboard button clicks (v2 dispatcher)."""
    query = update.callback_query
    await query.answer()

    # Option A: remove keyboard immediately to prevent double clicks
    # TODO: maybe replace with a no-op keyboard with one button? Spinner emoji then check_mark when done
    await query.edit_message_reply_markup(reply_markup=None)

    callback_data = query.data
    session = UserSession.from_context(context)

    handlers = {
        KeyboardActionType.ANALYZE: _handle_analyze,
        KeyboardActionType.CORRECT: _handle_correct,
        KeyboardActionType.REPHRASE: _handle_rephrase,
        KeyboardActionType.REPLY: _handle_reply,
    }
    handler = handlers.get(callback_data)
    if handler is None:
        logger.warning("Unknown callback_data: %s", callback_data)
        return

    replied = getattr(query.message, "reply_to_message", None)
    text = getattr(replied, "text", "") if replied else ""
    text = text.strip() if text else ""

    if not text:
        await send_response(
            bot=context.bot,
            chat_id=query.message.chat.id,
            text=t(MsgNoReplyText, session.base_language),
            reply_to_message_id=query.message.message_id,
        )
        return

    await handler(query, context, session, text)


def _format_dict_item(item: dict, primary_key: str | None = None) -> str:
    """Format a dict as HTML lines; optional primary_key shown in bold first."""
    key_order = [primary_key] if primary_key else []
    rest = [k for k in item if k != primary_key and item.get(k) not in (None, "")]
    for k in rest:
        if k not in key_order:
            key_order.append(k)
    lines = []
    for k in key_order:
        v = item.get(k)
        if v is None or v == "":
            continue
        v = str(v).strip()
        if k == primary_key:
            lines.append(f"• <b>{_escape_html(v)}</b>")
        else:
            label = k.replace("_", " ").title()
            lines.append(f"  <i>{label}</i>: {_escape_html(v)}")
    return "\n".join(lines) if lines else ""


def _escape_html(s: str) -> str:
    """Escape HTML specials for safe inclusion in message text."""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _format_analyze_result(raw: str) -> str:
    """Turn analyze JSON into readable HTML. Includes all keys from the raw dict."""
    # TODO: localise
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning("Analyze JSON decode error: %s", e)
        return "Analysis failed."

    if not isinstance(data, dict):
        return "Analysis failed."

    parts = []
    known_lists = {
        "vocabulary": "form_in_text",
        "grammar": "quote",
    }
    for key, value in data.items():
        if key in known_lists and isinstance(value, list):
            primary = known_lists[key]
            title = key.replace("_", " ").title()
            lines = [
                _format_dict_item(item if isinstance(item, dict) else {}, primary)
                for item in value
            ]
            block = "\n\n".join(line for line in lines if line.strip())
            if block:
                parts.append(f"<b>{title}</b>\n{block}")
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            title = key.replace("_", " ").title()
            lines = [_format_dict_item(i) for i in value]
            block = "\n\n".join(line for line in lines if line.strip())
            if block:
                parts.append(f"<b>{title}</b>\n{block}")
        elif isinstance(value, (str, int, float, bool)) and value:
            title = key.replace("_", " ").title()
            parts.append(f"<b>{title}</b>\n{_escape_html(str(value))}")
        elif isinstance(value, dict) and value:
            title = key.replace("_", " ").title()
            parts.append(f"<b>{title}</b>\n{_format_dict_item(value)}")

    if not parts:
        logger.warning("No vocabulary or grammar points for this text.")
        return "No vocabulary or grammar points for this text."
    return "\n\n".join(parts)


def _format_reply_result(raw: str) -> str:
    """Turn reply JSON array into readable HTML."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning("Reply JSON decode error: %s", e)
        return "Could not generate replies. Please try again."

    if not isinstance(data, list):
        return "Could not generate replies. Please try again."

    parts = []
    for item in data:
        if not isinstance(item, dict):
            continue
        reply = _escape_html(str(item.get("reply", "")).strip())
        tone = _escape_html(str(item.get("tone", "")).strip())
        if reply:
            line = f"• {reply}"
            if tone:
                line += f"  <i>({tone})</i>"
            parts.append(line)

    if not parts:
        return "Could not generate replies. Please try again."
    return "\n\n".join(parts)


def _format_rephrase_result(raw: str) -> str:
    """Turn rephrase JSON array into readable HTML."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning("Rephrase JSON decode error: %s", e)
        return "Could not generate rephrasings. Please try again."

    if not isinstance(data, list):
        return "Could not generate rephrasings. Please try again."

    parts = []
    for item in data:
        if not isinstance(item, dict):
            continue
        rephrasing = _escape_html(str(item.get("rephrasing", "")).strip())
        note = _escape_html(str(item.get("note", "")).strip())
        if rephrasing:
            line = f"• {rephrasing}"
            if note:
                line += f"  <i>({note})</i>"
            parts.append(line)

    if not parts:
        return "Could not generate rephrasings. Please try again."
    return "\n\n".join(parts)


async def _handle_analyze(
    query: CallbackQuery,
    context: ContextTypes.DEFAULT_TYPE,
    session: UserSession,
    text: str,
) -> None:
    """Handle the Analyze button click."""
    logger.info("Analyze button clicked (msg_id=%s)", query.message.message_id)
    msg = await send_response(
        bot=context.bot,
        chat_id=query.message.chat.id,
        text="Analyzing...",
        reply_to_message_id=query.message.message_id,
    )

    system_prompt = SYSTEM_PROMPT.format(
        base_language=session.base_language_name,
        target_language=session.target_language_name,
    )
    user_prompt = KEYBOARD_PROMPTS[KeyboardActionType.ANALYZE].format(
        base_language=session.base_language_name,
        target_language=session.target_language_name,
        text=text,
    )

    try:
        raw = await get_completion(system_prompt=system_prompt, user_prompt=user_prompt)
        logger.info("Analyze completion:\n{dump}", dump=json.dumps(json.loads(raw), indent=2, ensure_ascii=False))
        formatted = _format_analyze_result(raw)
    except Exception as e:
        logger.exception("Analyze completion failed: %s", e)
        # TODO: localise
        formatted = "Analysis failed. Please try again."

    # TODO: add a edit message abstraction for easy mocking in tests
    await context.bot.edit_message_text(
        chat_id=query.message.chat.id,
        message_id=msg.message_id,
        text=formatted,
        parse_mode="HTML",
    )
    # Re-attach keyboard to the original translation message so other actions remain available
    await context.bot.edit_message_reply_markup(
        chat_id=query.message.chat.id,
        message_id=query.message.message_id,
        reply_markup=KEYBOARD,
    )


async def _handle_correct(
    query: CallbackQuery,
    context: ContextTypes.DEFAULT_TYPE,
    session: UserSession,
    text: str,
) -> None:
    """Handle the Correct button click."""
    logger.info("Correct button clicked (msg_id=%s)", query.message.message_id)
    msg = await send_response(
        bot=context.bot,
        chat_id=query.message.chat.id,
        text="Correcting...",
        reply_to_message_id=query.message.message_id,
    )

    system_prompt = SYSTEM_PROMPT.format(
        base_language=session.base_language_name,
        target_language=session.target_language_name,
    )
    user_prompt = KEYBOARD_PROMPTS[KeyboardActionType.CORRECT].format(
        base_language=session.base_language_name,
        target_language=session.target_language_name,
        text=text,
    )

    try:
        formatted = await get_completion(system_prompt=system_prompt, user_prompt=user_prompt)
        logger.info("Correct completion received (msg_id=%s)", query.message.message_id)
    except Exception as e:
        logger.exception("Correct completion failed: %s", e)
        # TODO: localise
        formatted = "Correction failed. Please try again."

    await context.bot.edit_message_text(
        chat_id=query.message.chat.id,
        message_id=msg.message_id,
        text=formatted,
    )
    await context.bot.edit_message_reply_markup(
        chat_id=query.message.chat.id,
        message_id=query.message.message_id,
        reply_markup=KEYBOARD,
    )


async def _handle_rephrase(
    query: CallbackQuery,
    context: ContextTypes.DEFAULT_TYPE,
    session: UserSession,
    text: str,
) -> None:
    """Handle the Rephrase button click."""
    logger.info("Rephrase button clicked (msg_id=%s)", query.message.message_id)
    msg = await send_response(
        bot=context.bot,
        chat_id=query.message.chat.id,
        text="Rephrasing...",
        reply_to_message_id=query.message.message_id,
    )

    system_prompt = SYSTEM_PROMPT.format(
        base_language=session.base_language_name,
        target_language=session.target_language_name,
    )
    user_prompt = KEYBOARD_PROMPTS[KeyboardActionType.REPHRASE].format(
        base_language=session.base_language_name,
        target_language=session.target_language_name,
        text=text,
    )

    try:
        raw = await get_completion(system_prompt=system_prompt, user_prompt=user_prompt)
        logger.info("Rephrase completion received (msg_id=%s)", query.message.message_id)
        formatted = _format_rephrase_result(raw)
    except Exception as e:
        logger.exception("Rephrase completion failed: %s", e)
        # TODO: localise
        formatted = "Rephrasing failed. Please try again."

    await context.bot.edit_message_text(
        chat_id=query.message.chat.id,
        message_id=msg.message_id,
        text=formatted,
        parse_mode="HTML",
    )
    await context.bot.edit_message_reply_markup(
        chat_id=query.message.chat.id,
        message_id=query.message.message_id,
        reply_markup=KEYBOARD,
    )


async def _handle_reply(
    query: CallbackQuery,
    context: ContextTypes.DEFAULT_TYPE,
    session: UserSession,
    text: str,
) -> None:
    """Handle the Reply button click."""
    logger.info("Reply button clicked (msg_id=%s)", query.message.message_id)
    msg = await send_response(
        bot=context.bot,
        chat_id=query.message.chat.id,
        text="Generating replies...",
        reply_to_message_id=query.message.message_id,
    )

    system_prompt = SYSTEM_PROMPT.format(
        base_language=session.base_language_name,
        target_language=session.target_language_name,
    )
    user_prompt = KEYBOARD_PROMPTS[KeyboardActionType.REPLY].format(
        base_language=session.base_language_name,
        target_language=session.target_language_name,
        n=N_SUGGESTED_REPLIES,
        text=text,
    )

    try:
        raw = await get_completion(system_prompt=system_prompt, user_prompt=user_prompt)
        logger.info("Reply completion:\n{dump}", dump=json.dumps(json.loads(raw), indent=2, ensure_ascii=False))
        formatted = _format_reply_result(raw)
    except Exception as e:
        logger.exception("Reply completion failed: %s", e)
        # TODO: localise
        formatted = "Could not generate replies. Please try again."

    await context.bot.edit_message_text(
        chat_id=query.message.chat.id,
        message_id=msg.message_id,
        text=formatted,
        parse_mode="HTML",
    )
    await context.bot.edit_message_reply_markup(
        chat_id=query.message.chat.id,
        message_id=query.message.message_id,
        reply_markup=KEYBOARD,
    )
