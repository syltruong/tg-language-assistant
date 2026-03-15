from loguru import logger
from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.handlers_v2.response import send_response
from bot.session import UserSession
from bot.types import KeyboardActionType

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

    await handler(query, context, session)


async def _handle_analyze(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, session: UserSession) -> None:
    """Handle the Analyze button click."""
    logger.info("Analyze button clicked (msg_id=%s)", query.message.message_id)
    msg = await send_response(
        bot=context.bot,
        chat_id=query.message.chat.id,
        text="Analyzing...",
        reply_to_message_id=query.message.message_id,
    )
    # TODO: load prompt from prompts_v2/buttons/analyze.md, call LLM, send response


async def _handle_correct(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, session: UserSession) -> None:
    """Handle the Correct button click."""
    logger.info("Correct button clicked (msg_id=%s)", query.message.message_id)
    msg = await send_response(
        bot=context.bot,
        chat_id=query.message.chat.id,
        text="Correcting...",
        reply_to_message_id=query.message.message_id,
    )
    # TODO: load prompt from prompts_v2/buttons/correct.md, call LLM, send response


async def _handle_rephrase(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, session: UserSession) -> None:
    """Handle the Rephrase button click."""
    logger.info("Rephrase button clicked (msg_id=%s)", query.message.message_id)
    msg = await send_response(
        bot=context.bot,
        chat_id=query.message.chat.id,
        text="Rephrasing...",
        reply_to_message_id=query.message.message_id,
    )
    # TODO: load prompt from prompts_v2/buttons/rephrase.md, call LLM, send response


async def _handle_reply(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, session: UserSession) -> None:
    """Handle the Reply button click."""
    logger.info("Reply button clicked (msg_id=%s)", query.message.message_id)
    msg = await send_response(
        bot=context.bot,
        chat_id=query.message.chat.id,
        text="Replies...",
        reply_to_message_id=query.message.message_id,
    )
    # TODO: load prompt from prompts_v2/buttons/reply.md, call LLM, send response
