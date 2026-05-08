"""Per-user session state backed by ``context.user_data``.

Wraps the raw dict access patterns used throughout the handlers into a
single, typed abstraction.  This makes state access self-documenting,
centralises defaults, and provides a clean seam for swapping in a
persistent storage backend later.
"""

from __future__ import annotations

import contextlib

from telegram.ext import ContextTypes

from bot.actions.verbs.base import LanguagePair
from bot.config.lang import LANGUAGE_NAMES
from bot.types import ActionType, ReplySuggestion

_MAX_ACTIVE_MESSAGES = 5


class UserSession:
    """
    Thin wrapper around a ``context.user_data`` dict.

    context.user_data: {
        _KEY_MESSAGES : { msg_id: text },
        _KEY_DETECTED_LANGUAGE : { msg_id: language },
        _KEY_ACTION_TYPES : { msg_id: list[ActionType] },
        _KEY_REPLIES : { msg_id: list[replies] },
        _KEY_ACTIVE_MESSAGES : [msg_id, ...],
    }
    """

    _KEY_BASE_LANGUAGE = "base_language"
    _KEY_TARGET_LANGUAGE = "target_language"
    _KEY_MESSAGES = "messages"
    _KEY_DETECTED_LANGUAGE = "detected_language"
    _KEY_ACTION_TYPES = "action_types"
    _KEY_REPLIES = "replies"
    _KEY_ACTIVE_MESSAGES = "active_message_ids"
    _KEY_KEYBOARD_IDS = "keyboard_ids"

    _DEFAULT_BASE_LANGUAGE = "en"
    _DEFAULT_TARGET_LANGUAGE = "fr"

    def __init__(self, user_data: dict) -> None:
        # Direct reference — mutations to self._data write through to context.user_data immediately; no flush needed.
        self._data = user_data

    @classmethod
    def from_context(cls, context: ContextTypes.DEFAULT_TYPE) -> UserSession:
        return cls(context.user_data)

    # ── user preferences ─────────────────────────────────────────

    @property
    def base_language(self) -> str:
        return self._data.get(self._KEY_BASE_LANGUAGE, self._DEFAULT_BASE_LANGUAGE)

    @base_language.setter
    def base_language(self, value: str) -> None:
        self._data[self._KEY_BASE_LANGUAGE] = value

    @property
    def target_language(self) -> str:
        return self._data.get(self._KEY_TARGET_LANGUAGE, self._DEFAULT_TARGET_LANGUAGE)

    @target_language.setter
    def target_language(self, value: str) -> None:
        self._data[self._KEY_TARGET_LANGUAGE] = value

    @property
    def base_language_name(self) -> str:
        return LANGUAGE_NAMES[self.base_language]

    @property
    def target_language_name(self) -> str:
        return LANGUAGE_NAMES[self.target_language]

    @property
    def language_pair(self) -> LanguagePair:
        return LanguagePair(base=self.base_language, target=self.target_language)

    def get_keyboard_id(self, anchor_id: int) -> int | None:
        return self._data.get(self._KEY_KEYBOARD_IDS, {}).get(anchor_id)

    def set_keyboard_id(self, anchor_id: int, keyboard_id: int) -> None:
        self._data.setdefault(self._KEY_KEYBOARD_IDS, {})[anchor_id] = keyboard_id

    # ── per-message state ────────────────────────────────────────

    def store_original_trigger_message(
        self,
        msg_id: int,
        text: str,
        detected_language: str,
        action_types: list[ActionType],
    ) -> None:
        self._data.setdefault(self._KEY_MESSAGES, {})[msg_id] = text
        self._data.setdefault(
            self._KEY_DETECTED_LANGUAGE,
            {},
        )[msg_id] = detected_language
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

    # ── active-message tracking ──────────────────────────────────

    def get_active_messages(self) -> list[int]:
        return self._data.get(self._KEY_ACTIVE_MESSAGES, [])

    def add_active_message(self, msg_id: int) -> None:
        ids = self._data.setdefault(self._KEY_ACTIVE_MESSAGES, [])
        ids.append(msg_id)
        if len(ids) > _MAX_ACTIVE_MESSAGES:
            ids.pop(0)

    def remove_active_message(self, msg_id: int) -> None:
        ids = self._data.get(self._KEY_ACTIVE_MESSAGES, [])
        with contextlib.suppress(ValueError):
            ids.remove(msg_id)
