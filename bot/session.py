"""Per-user session state backed by ``context.user_data`` for ephemeral state
and a ``UserRepository`` for persistent preferences.
"""

from __future__ import annotations

import contextlib

from telegram.ext import ContextTypes

from bot.config.lang import LANGUAGE_NAMES
from bot.types import ActionType, ReplySuggestion
from bot.user_repository import UserPreferences, UserRepository

_MAX_ACTIVE_MESSAGES = 5


class UserSession:
    """
    Combines a persistent preference store (UserRepository) with an ephemeral
    per-request dict (context.user_data) for transient state such as message
    history and active message IDs.

    Preferences (base_language, target_language, instant_action) are read from
    and written to the repository.  Everything else remains in context.user_data.

    context.user_data: {
        _KEY_MESSAGES : { msg_id: text },
        _KEY_DETECTED_LANGUAGE : { msg_id: language },
        _KEY_ACTION_TYPES : { msg_id: list[ActionType] },
        _KEY_REPLIES : { msg_id: list[replies] },
        _KEY_ACTIVE_MESSAGES : [msg_id, ...],
    }
    """

    _KEY_MESSAGES = "messages"
    _KEY_DETECTED_LANGUAGE = "detected_language"
    _KEY_ACTION_TYPES = "action_types"
    _KEY_REPLIES = "replies"
    _KEY_ACTIVE_MESSAGES = "active_message_ids"

    def __init__(
        self,
        user_data: dict,
        preferences: UserPreferences,
        repo: UserRepository,
        user_id: int,
    ) -> None:
        self._data = user_data
        self._preferences = preferences
        self._repo = repo
        self._user_id = user_id

    @classmethod
    async def from_context(
        cls,
        context: ContextTypes.DEFAULT_TYPE,
        user_id: int,
        repo: UserRepository,
    ) -> UserSession:
        prefs = await repo.get_preferences(user_id)
        return cls(
            user_data=context.user_data,
            preferences=prefs,
            repo=repo,
            user_id=user_id,
        )

    # ── user preferences ─────────────────────────────────────────

    @property
    def base_language(self) -> str:
        return self._preferences.base_language

    async def set_base_language(self, value: str) -> None:
        self._preferences = self._preferences.model_copy(
            update={"base_language": value}
        )
        await self._repo.save_preferences(self._user_id, self._preferences)

    @property
    def target_language(self) -> str:
        return self._preferences.target_language

    async def set_target_language(self, value: str) -> None:
        self._preferences = self._preferences.model_copy(
            update={"target_language": value}
        )
        await self._repo.save_preferences(self._user_id, self._preferences)

    @property
    def base_language_name(self) -> str:
        return LANGUAGE_NAMES[self.base_language]

    @property
    def target_language_name(self) -> str:
        return LANGUAGE_NAMES[self.target_language]

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
