"""Per-user session state backed by ``context.user_data``.

Wraps the raw dict access patterns used throughout the handlers into a
single, typed abstraction.  This makes state access self-documenting,
centralises defaults, and provides a clean seam for swapping in a
persistent storage backend later.
"""

from __future__ import annotations

from telegram.ext import ContextTypes

from bot.types import ReplySuggestion


class UserSession:
    """Thin wrapper around a ``context.user_data`` dict."""

    _KEY_MESSAGES = "messages"
    _KEY_MODES = "modes"
    _KEY_REPLIES = "replies"

    def __init__(self, user_data: dict) -> None:
        self._data = user_data

    @classmethod
    def from_context(cls, context: ContextTypes.DEFAULT_TYPE) -> UserSession:
        return cls(context.user_data)

    def store_message(self, msg_id: int, text: str, mode: KeyboardMode) -> None:
        self._data.setdefault(self._KEY_MESSAGES, {})[msg_id] = text
        self._data.setdefault(self._KEY_MODES, {})[msg_id] = mode

    def get_message(self, msg_id: int) -> str:
        return self._data.get(self._KEY_MESSAGES, {}).get(msg_id, "")

    def get_mode(self, msg_id: int) -> KeyboardMode:
        return self._data.get(self._KEY_MODES, {}).get(msg_id, KeyboardMode.FULL)

    def store_replies(self, msg_id: int, replies: list[ReplySuggestion]) -> None:
        self._data.setdefault(self._KEY_REPLIES, {})[msg_id] = replies

    def get_replies(self, msg_id: int) -> list[ReplySuggestion]:
        return self._data.get(self._KEY_REPLIES, {}).get(msg_id, [])
