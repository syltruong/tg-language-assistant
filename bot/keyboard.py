from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def make_keyboard() -> InlineKeyboardMarkup:
    """Return the standard action keyboard with a cancel/clear button."""
    keyboard = [
        [
            InlineKeyboardButton("🧠 Translate", callback_data="translate"),
            InlineKeyboardButton("🍎 Vocab", callback_data="vocab"),
        ],
        [
            InlineKeyboardButton("🧑‍💻 Syntax", callback_data="syntax"),
            InlineKeyboardButton("💬 Reply", callback_data="reply"),
        ],
        [
            InlineKeyboardButton("✏️ Correct", callback_data="correct"),
        ],
        [
            InlineKeyboardButton("Cancel", callback_data="clear"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
