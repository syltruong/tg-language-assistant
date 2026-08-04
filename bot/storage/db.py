"""SQLite connection and schema migrations.

Implements the repository abstraction's storage layer per ADR-0001: a single
file, no server, swappable behind the repository interfaces that sit on top.

Schema versioning uses SQLite's built-in ``PRAGMA user_version`` rather than a
bookkeeping table — the migrations are numbered files on disk, so there is
nothing to record beyond "how far have we got".
"""

from __future__ import annotations

from pathlib import Path

import aiosqlite
from loguru import logger

_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


class Database:
    """Owns the connection and brings the schema up to date on connect."""

    def __init__(
        self,
        path: str | Path,
        migrations_dir: Path = _MIGRATIONS_DIR,
    ) -> None:
        self._path = Path(path)
        self._migrations_dir = migrations_dir
        self._connection: aiosqlite.Connection | None = None

    @property
    def connection(self) -> aiosqlite.Connection:
        if self._connection is None:
            raise RuntimeError("Database is not connected. Call connect() first.")
        return self._connection

    async def connect(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self._path)
        self._connection.row_factory = aiosqlite.Row
        await self._migrate()

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def _migrate(self) -> None:
        current = await self._current_version()

        for version, path in self._pending(current):
            logger.info("Applying migration {}", path.name)
            await self.connection.executescript(path.read_text(encoding="utf-8"))
            # PRAGMA does not accept bound parameters; version is an int parsed
            # from a filename we control.
            await self.connection.execute(f"PRAGMA user_version = {version}")
            await self.connection.commit()

    async def _current_version(self) -> int:
        cursor = await self.connection.execute("PRAGMA user_version")
        row = await cursor.fetchone()
        return row[0]

    def _pending(self, current: int) -> list[tuple[int, Path]]:
        migrations = [
            (int(path.name.split("_")[0]), path)
            for path in self._migrations_dir.glob("*.sql")
        ]
        return sorted((m for m in migrations if m[0] > current), key=lambda m: m[0])
