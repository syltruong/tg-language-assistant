from telegram import InlineKeyboardButton, InlineKeyboardMarkup

_CANCEL_ROW = [InlineKeyboardButton("Cancel", callback_data="clear")]


def make_keyboard(mode: str = "full") -> InlineKeyboardMarkup:
    """Return an inline keyboard whose buttons depend on *mode*.

    ``"full"``           – 2x2 grid with all actions (target-language input).
    ``"translate_only"`` – single Translate button (source-language input).
    """
    if mode == "translate_only":
        keyboard = [
            [InlineKeyboardButton("🧠 Translate", callback_data="translate")],
            _CANCEL_ROW,
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton("🧠 Translate", callback_data="translate"),
                InlineKeyboardButton("📖 Analyze", callback_data="analyze"),
            ],
            [
                InlineKeyboardButton("💬 Reply", callback_data="reply"),
                InlineKeyboardButton("✏️ Correct", callback_data="correct"),
            ],
            _CANCEL_ROW,
        ]
    return InlineKeyboardMarkup(keyboard)
