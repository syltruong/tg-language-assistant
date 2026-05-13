"""Inline keyboard definition shared across triggers."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.types import KeyboardActionType, Suggestion

BUTTON_TITLES: dict[KeyboardActionType, str] = {
    KeyboardActionType.ANALYZE: "📖 Analyze",
    KeyboardActionType.CORRECT: "✏️ Correct",
    KeyboardActionType.REPHRASE: "🧠 Rephrase",
    KeyboardActionType.REPLY: "💬 Reply",
}

SELECT_PREFIX = "select:"


def build_suggestions_keyboard(suggestions: list[Suggestion]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(f"{i + 1} · {s.note}", callback_data=f"{SELECT_PREFIX}{i}")]
            for i, s in enumerate(suggestions)
        ]
    )


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
