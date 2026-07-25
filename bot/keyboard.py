"""Inline keyboard definition shared across triggers."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config.messages import MsgRateThisResponse, MsgSave, MsgSaved, t
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
SAVE_PREFIX = "save:"
SAVE = f"{SAVE_PREFIX}insight"


def _rating_rows() -> list[list[InlineKeyboardButton]]:
    """A label row followed by the thumbs row, visually separating rating from actions."""
    return [
        [InlineKeyboardButton(t(MsgRateThisResponse), callback_data=RATE_LABEL)],
        [
            InlineKeyboardButton("👍", callback_data=RATE_UP),
            InlineKeyboardButton("👎", callback_data=RATE_DOWN),
        ],
    ]


def _is_rating_row(row) -> bool:
    return any((btn.callback_data or "").startswith(RATE_PREFIX) for btn in row)


def strip_rating_rows(markup: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    """Return a copy of markup with the rating label + thumbs rows removed.

    Identifies the rows by their callback data rather than by position, so
    adding a row to the keyboard cannot silently strip the wrong one.
    """
    return InlineKeyboardMarkup(
        [row for row in markup.inline_keyboard if not _is_rating_row(row)]
    )


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


def build_action_keyboard(saved: bool = False) -> InlineKeyboardMarkup:
    """The standard keyboard for a Conversation Turn.

    Built per message rather than once at import, because the Save button
    reflects whether this turn has already been kept.
    """
    return InlineKeyboardMarkup(
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
            [InlineKeyboardButton(t(MsgSaved if saved else MsgSave), callback_data=SAVE)],
            *_rating_rows(),
        ]
    )
