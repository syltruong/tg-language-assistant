"""UserRepository protocol and implementations.

Protocol: UserRepository
Implementations: SqliteUserRepository (aiosqlite-backed), FakeUserRepository (in-memory)
"""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable

import aiosqlite
from pydantic import BaseModel

from bot.types import InstantActionType


class UserPreferences(BaseModel):
    base_language: str = "en"
    target_language: str = "fr"
    instant_action: InstantActionType = InstantActionType.TRANSLATE


@runtime_checkable
class UserRepository(Protocol):
    async def get_preferences(self, user_id: int) -> UserPreferences: ...
    async def save_preferences(self, user_id: int, prefs: UserPreferences) -> None: ...


_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id INTEGER PRIMARY KEY,
    base_language TEXT NOT NULL DEFAULT 'en',
    target_language TEXT NOT NULL DEFAULT 'fr',
    instant_action TEXT NOT NULL DEFAULT 'translate'
)
"""


class SqliteUserRepository:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._initialised = False

    async def _ensure_schema(self, conn: aiosqlite.Connection) -> None:
        if not self._initialised:
            await conn.execute(_CREATE_TABLE_SQL)
            await conn.commit()
            self._initialised = True

    async def get_preferences(self, user_id: int) -> UserPreferences:
        async with aiosqlite.connect(self._db_path) as conn:
            await self._ensure_schema(conn)
            async with conn.execute(
                "SELECT base_language, target_language, instant_action "
                "FROM user_preferences WHERE user_id = ?",
                (user_id,),
            ) as cursor:
                row = await cursor.fetchone()
        if row is None:
            return UserPreferences()
        base_language, target_language, instant_action = row
        return UserPreferences(
            base_language=base_language,
            target_language=target_language,
            instant_action=InstantActionType(instant_action),
        )

    async def save_preferences(self, user_id: int, prefs: UserPreferences) -> None:
        async with aiosqlite.connect(self._db_path) as conn:
            await self._ensure_schema(conn)
            await conn.execute(
                "INSERT OR REPLACE INTO user_preferences "
                "(user_id, base_language, target_language, instant_action) "
                "VALUES (?, ?, ?, ?)",
                (
                    user_id,
                    prefs.base_language,
                    prefs.target_language,
                    prefs.instant_action,
                ),
            )
            await conn.commit()

    @classmethod
    def from_env(cls) -> SqliteUserRepository:
        db_path = os.environ.get("SQLITE_DB_PATH", "userdata.db")
        return cls(db_path)


class FakeUserRepository:
    def __init__(self) -> None:
        self._store: dict[int, UserPreferences] = {}

    async def get_preferences(self, user_id: int) -> UserPreferences:
        return self._store.get(user_id, UserPreferences())

    async def save_preferences(self, user_id: int, prefs: UserPreferences) -> None:
        self._store[user_id] = prefs
