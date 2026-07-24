"""Inline keyboard definition shared across triggers."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config.messages import MsgRateThisResponse, t
from bot.types import KeyboardActionType, Suggestion

BUTTON_TITLES: dict[KeyboardActionType, str] = {
    KeyboardActionType.ANALYZE: "📖 Analyze",
    KeyboardActionType.CORRECT: "✏️ Correct",
    KeyboardActionType.REPHRASE: "🧠 Rephrase",
    KeyboardActionType.REPLY: "💬 Reply",
}

SELECT_PREFIX = "select:"
LANG_TARGET_PREFIX = "lang_target:"
RATE_PREFIX = "rate:"
RATE_UP = f"{RATE_PREFIX}up"
RATE_DOWN = f"{RATE_PREFIX}down"
RATE_LABEL = f"{RATE_PREFIX}label"


def _rating_rows() -> list[list[InlineKeyboardButton]]:
    """A label row followed by the thumbs row, visually separating rating from actions."""
    return [
        [InlineKeyboardButton(t(MsgRateThisResponse), callback_data=RATE_LABEL)],
        [
            InlineKeyboardButton("👍", callback_data=RATE_UP),
            InlineKeyboardButton("👎", callback_data=RATE_DOWN),
        ],
    ]


def strip_rating_rows(markup: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    """Return a copy of markup with its last two rows (the rating label + thumbs rows) removed."""
    return InlineKeyboardMarkup(list(markup.inline_keyboard[:-2]))


def build_language_keyboard(languages: dict) -> InlineKeyboardMarkup:
    from bot.config.lang import LANGUAGE_DISPLAY_NAMES, LANGUAGE_FLAGS
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(
                f"{LANGUAGE_FLAGS.get(code, '')} {LANGUAGE_DISPLAY_NAMES.get(code, lang.name.title())}".strip(),
                callback_data=f"{LANG_TARGET_PREFIX}{code}",
            )]
            for lang, code in languages.items()
        ]
    )


def build_suggestions_keyboard(suggestions: list[Suggestion]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(f"{i + 1} · {s.note}", callback_data=f"{SELECT_PREFIX}{i}")]
            for i, s in enumerate(suggestions)
        ]
        + _rating_rows()
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
        *_rating_rows(),
    ]
)
