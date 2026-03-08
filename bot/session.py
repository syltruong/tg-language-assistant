"""Per-user session state backed by ``context.user_data``.

Wraps the raw dict access patterns used throughout the handlers into a
single, typed abstraction.  This makes state access self-documenting,
centralises defaults, and provides a clean seam for swapping in a
persistent storage backend later.
"""

from __future__ import annotations

from telegram.ext import ContextTypes

from bot.types import ActionType, ReplySuggestion


class UserSession:
    """
    Thin wrapper around a ``context.user_data`` dict.

    context.user_data: {
        _KEY_MESSAGES : { msg_id: text },
        _KEY_DETECTED_LANGUAGE : { msg_id: language },
        _KEY_ACTION_TYPES : { msg_id: list[ActionType] },
        _KEY_REPLIES : { msg_id: list[replies] },
    }
    """

    _KEY_MESSAGES = "messages"
    _KEY_DETECTED_LANGUAGE = "detected_language"
    _KEY_ACTION_TYPES = "action_types"
    _KEY_REPLIES = "replies"

    def __init__(self, user_data: dict) -> None:
        self._data = user_data

    @classmethod
    def from_context(cls, context: ContextTypes.DEFAULT_TYPE) -> UserSession:
        return cls(context.user_data)

    def store_original_trigger_message(self, msg_id: int, text: str, detected_language: str, action_types: list[ActionType]) -> None:
        self._data.setdefault(self._KEY_MESSAGES, {})[msg_id] = text
        self._data.setdefault(self._KEY_DETECTED_LANGUAGE, {})[msg_id] = detected_language
        self._data.setdefault(self._KEY_ACTION_TYPES, {})[msg_id] = action_types

    def get_message(self, msg_id: int) -> str:
        return self._data.get(self._KEY_MESSAGES, {}).get(msg_id, "")

    def get_detected_language(self, msg_id: int) -> str:
        return self._data.get(self._KEY_DETECTED_LANGUAGE, {}).get(msg_id, "")

    def get_action_types(self, msg_id: int) -> list[ActionType]:
        return self._data.get(self._KEY_ACTION_TYPES, {}).get(msg_id, [])

    def store_replies(self, msg_id: int, replies: list[ReplySuggestion]) -> None:
        self._data.setdefault(self._KEY_REPLIES, {})[msg_id] = replies

    def get_replies(self, msg_id: int) -> list[ReplySuggestion]:
        return self._data.get(self._KEY_REPLIES, {}).get(msg_id, [])
