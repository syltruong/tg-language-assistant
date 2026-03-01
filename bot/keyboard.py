from telegram import InlineKeyboardButton, InlineKeyboardMarkup

_CANCEL_ROW = [InlineKeyboardButton("Cancel", callback_data="clear")]

_NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


def make_reply_keyboard(n: int) -> InlineKeyboardMarkup:
    """Return a keyboard with *n* numbered reply buttons and a Back button."""
    reply_row = [
        InlineKeyboardButton(_NUMBER_EMOJIS[i], callback_data=f"reply_{i}")
        for i in range(n)
    ]
    return InlineKeyboardMarkup([
        reply_row,
        [InlineKeyboardButton("⬅️ Back", callback_data="back")],
    ])


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
