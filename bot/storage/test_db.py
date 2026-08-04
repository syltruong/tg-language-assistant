from bot.storage.db import Database


class TestDatabaseSchema:
    async def test_connecting_to_a_fresh_file_creates_the_saved_insights_table(self, tmp_path):
        db = Database(path=tmp_path / "bot.db")

        await db.connect()

        cursor = await db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'saved_insights'"
        )
        assert await cursor.fetchone() is not None

        await db.close()

    async def test_reopening_an_existing_database_preserves_stored_rows(self, tmp_path):
        """Migrations must not re-run over a populated database."""
        path = tmp_path / "bot.db"
        first = Database(path=path)
        await first.connect()
        await first.connection.execute(
            """
            INSERT INTO saved_insights (
                user_id, chat_id, slot_message_id, anchor_text, detected_language,
                base_language, target_language, action_type, result_text, created_at
            ) VALUES (1, 2, 3, 'bonjour', 'fr', 'en', 'fr', 'analyze', 'a greeting', '2026-07-25')
            """
        )
        await first.connection.commit()
        await first.close()

        second = Database(path=path)
        await second.connect()

        cursor = await second.connection.execute("SELECT anchor_text FROM saved_insights")
        assert (await cursor.fetchone())["anchor_text"] == "bonjour"

        await second.close()


class TestDatabaseMigrations:
    async def test_applies_migrations_in_filename_order(self, tmp_path):
        """0002 alters a table 0001 creates — the wrong order raises 'no such table'."""
        migrations = tmp_path / "migrations"
        migrations.mkdir()
        (migrations / "0001_create.sql").write_text("CREATE TABLE widgets (id INTEGER);")
        (migrations / "0002_alter.sql").write_text("ALTER TABLE widgets ADD COLUMN label TEXT;")

        db = Database(path=tmp_path / "bot.db", migrations_dir=migrations)
        await db.connect()

        cursor = await db.connection.execute("SELECT id, label FROM widgets")
        assert await cursor.fetchall() == []

        await db.close()

    async def test_applies_only_migrations_newer_than_the_current_version(self, tmp_path):
        """A migration added after the first deploy is picked up on next connect."""
        migrations = tmp_path / "migrations"
        migrations.mkdir()
        (migrations / "0001_create.sql").write_text("CREATE TABLE widgets (id INTEGER);")
        path = tmp_path / "bot.db"

        first = Database(path=path, migrations_dir=migrations)
        await first.connect()
        await first.close()

        (migrations / "0002_alter.sql").write_text("ALTER TABLE widgets ADD COLUMN label TEXT;")
        second = Database(path=path, migrations_dir=migrations)
        await second.connect()

        cursor = await second.connection.execute("SELECT label FROM widgets")
        assert await cursor.fetchall() == []

        await second.close()
