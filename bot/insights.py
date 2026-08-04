"""Saved Insights — the explicit memory capability's write and read model.

A Saved Insight is an immutable snapshot of one Conversation Turn the user
chose to keep. Per ADR-0006 the write path stores raw material verbatim: no
LLM call, no interpretation, no distillation. Anything derived (titles,
vocabulary, review schedules) is a read-side concern that can be recomputed
for as long as the row exists.

The protocol and its fake live together here, following the pattern
established by the LLM Interface and Response Publisher.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

import aiosqlite

from bot.storage.db import Database

_DEFAULT_LIMIT = 20

_COLUMNS = """
    user_id, chat_id, slot_message_id, anchor_text, detected_language,
    base_language, target_language, action_type, result_text, parse_mode,
    run_id, created_at
"""


@dataclass(frozen=True, slots=True)
class SavedInsight:
    """One kept turn. ``id`` and ``created_at`` are assigned by the repository."""

    user_id: int
    chat_id: int
    slot_message_id: int
    anchor_text: str
    detected_language: str
    base_language: str
    target_language: str
    action_type: str
    result_text: str
    parse_mode: str | None = None
    run_id: str | None = None
    created_at: str | None = None
    id: int | None = None


@runtime_checkable
class InsightRepositoryProtocol(Protocol):
    async def save(self, insight: SavedInsight) -> int | None:
        """Store an insight. Returns its id, or None if this turn+action is already kept."""
        ...

    async def list_for_user(
        self, user_id: int, limit: int = _DEFAULT_LIMIT
    ) -> list[SavedInsight]: ...


class InMemoryInsightRepository:
    """Fake for tests and local development."""

    def __init__(self) -> None:
        self._insights: list[SavedInsight] = []
        self._next_id = 1

    async def save(self, insight: SavedInsight) -> int | None:
        if any(_turn_key(stored) == _turn_key(insight) for stored in self._insights):
            return None

        stored = replace(insight, id=self._next_id, created_at=_now())
        self._insights.append(stored)
        self._next_id += 1
        return stored.id

    async def list_for_user(
        self, user_id: int, limit: int = _DEFAULT_LIMIT
    ) -> list[SavedInsight]:
        matching = [i for i in self._insights if i.user_id == user_id]
        return sorted(matching, key=lambda i: i.id, reverse=True)[:limit]


class SqliteInsightRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    async def save(self, insight: SavedInsight) -> int | None:
        try:
            cursor = await self._database.connection.execute(
                f"""
                INSERT INTO saved_insights ({_COLUMNS})
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    insight.user_id,
                    insight.chat_id,
                    insight.slot_message_id,
                    insight.anchor_text,
                    insight.detected_language,
                    insight.base_language,
                    insight.target_language,
                    insight.action_type,
                    insight.result_text,
                    insight.parse_mode,
                    insight.run_id,
                    _now(),
                ),
            )
        except aiosqlite.IntegrityError:
            # The UNIQUE constraint — this turn and action are already kept.
            return None

        await self._database.connection.commit()
        return cursor.lastrowid

    async def list_for_user(
        self, user_id: int, limit: int = _DEFAULT_LIMIT
    ) -> list[SavedInsight]:
        cursor = await self._database.connection.execute(
            f"""
            SELECT id, {_COLUMNS} FROM saved_insights
            WHERE user_id = ? AND deleted_at IS NULL
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        return [_from_row(row) for row in await cursor.fetchall()]


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _turn_key(insight: SavedInsight) -> tuple[int, int, int, str]:
    """The natural key mirroring the table's UNIQUE constraint."""
    return (insight.user_id, insight.chat_id, insight.slot_message_id, insight.action_type)


def _from_row(row: aiosqlite.Row) -> SavedInsight:
    return SavedInsight(**dict(row))
