"""Inline keyboard definition shared across triggers."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.types import KeyboardActionType

BUTTON_TITLES: dict[KeyboardActionType, str] = {
    KeyboardActionType.ANALYZE: "📖 Analyze",
    KeyboardActionType.CORRECT: "✏️ Correct",
    KeyboardActionType.REPHRASE: "🧠 Rephrase",
    KeyboardActionType.REPLY: "💬 Reply",
}

KEYBOARD = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                BUTTON_TITLES[KeyboardActionType.ANALYZE],
                callback_data=KeyboardActionType.ANALYZE,
            ),
            InlineKeyboardButton(
                BUTTON_TITLES[KeyboardActionType.CORRECT],
                callback_data=KeyboardActionType.CORRECT,
            ),
        ],
        [
            InlineKeyboardButton(
                BUTTON_TITLES[KeyboardActionType.REPHRASE],
                callback_data=KeyboardActionType.REPHRASE,
            ),
            InlineKeyboardButton(
                BUTTON_TITLES[KeyboardActionType.REPLY],
                callback_data=KeyboardActionType.REPLY,
            ),
        ],
    ]
)
