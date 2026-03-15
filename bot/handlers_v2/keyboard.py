from loguru import logger
from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.handlers_v2.response import send_response
from bot.session import UserSession
from bot.types import ActionType

ACTION_TITLES: dict[ActionType, str] = {
    ActionType.ANALYZE: "📖 Analyze",
    ActionType.CORRECT: "✏️ Correct",
    ActionType.REPHRASE: "🔄 Rephrase",
    ActionType.REPLY: "💬 Reply",
}

BUTTON_ACTIONS = list(ACTION_TITLES.keys())

KEYBOARD = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(ACTION_TITLES[ActionType.ANALYZE], callback_data=ActionType.ANALYZE),
            InlineKeyboardButton(ACTION_TITLES[ActionType.CORRECT], callback_data=ActionType.CORRECT),
        ],
        [
            InlineKeyboardButton(ACTION_TITLES[ActionType.REPHRASE], callback_data=ActionType.REPHRASE),
            InlineKeyboardButton(ACTION_TITLES[ActionType.REPLY], callback_data=ActionType.REPLY),
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
        ActionType.ANALYZE: _handle_analyze,
        ActionType.CORRECT: _handle_correct,
        ActionType.REPHRASE: _handle_rephrase,
        ActionType.REPLY: _handle_reply,
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
