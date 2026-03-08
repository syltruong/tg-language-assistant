from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.types import ActionType

ACTION_TITLES: dict[ActionType, str] = {
    ActionType.TRANSLATE: "🧠 Translate",
    ActionType.ANALYZE: "📖 Analyze",
    ActionType.REPLY: "💬 Reply",
    ActionType.CORRECT: "✏️ Correct",
}

NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

_CANCEL_ROW = [InlineKeyboardButton("Cancel", callback_data="clear")]

def make_reply_keyboard(n: int) -> InlineKeyboardMarkup:
    """Return a keyboard with *n* numbered reply buttons and a Back button."""
    reply_row = [
        InlineKeyboardButton(NUMBER_EMOJIS[i], callback_data=f"reply_{i}")
        for i in range(n)
    ]
    return InlineKeyboardMarkup([
        reply_row,
        [InlineKeyboardButton("⬅️ Back", callback_data="back")],
    ])


def make_keyboard(action_types: list[ActionType] = [
    ActionType.TRANSLATE,
    ActionType.ANALYZE,
    ActionType.REPLY,
    ActionType.CORRECT,
]) -> InlineKeyboardMarkup:
    """Return an inline keyboard whose buttons depend on action_types
    """

    def _btn(action: ActionType) -> InlineKeyboardButton:
        return InlineKeyboardButton(ACTION_TITLES[action], callback_data=action)

    buttons = [_btn(action) for action in action_types]
    row_size = 2

    keyboard = [
        buttons[i:i + row_size] for i in range(0, len(buttons), row_size)
    ] + [_CANCEL_ROW]
    return InlineKeyboardMarkup(keyboard)
