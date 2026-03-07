from bot.config import ALLOWED_USERS


def _is_authorized(user_id: int | None) -> bool:
    """Return True if the user is allowed to use the bot."""
    if not ALLOWED_USERS:
        return True
    return user_id in ALLOWED_USERS
