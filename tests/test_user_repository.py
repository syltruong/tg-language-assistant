"""Tests for UserRepository implementations and UserPreferences model."""

from bot.types import InstantActionType
from bot.user_repository import (
    FakeUserRepository,
    SqliteUserRepository,
    UserPreferences,
)


class TestUserPreferences:
    def test_defaults(self):
        prefs = UserPreferences()
        assert prefs.base_language == "en"
        assert prefs.target_language == "fr"
        assert prefs.instant_action == InstantActionType.TRANSLATE

    def test_custom_values(self):
        prefs = UserPreferences(
            base_language="fr",
            target_language="en",
            instant_action=InstantActionType.TRANSLATE_WITH_CONTEXT,
        )
        assert prefs.base_language == "fr"
        assert prefs.target_language == "en"
        assert prefs.instant_action == InstantActionType.TRANSLATE_WITH_CONTEXT

    def test_model_copy_update(self):
        prefs = UserPreferences()
        updated = prefs.model_copy(update={"base_language": "de"})
        assert updated.base_language == "de"
        assert prefs.base_language == "en"


class TestFakeUserRepository:
    async def test_returns_defaults_for_unknown_user(self):
        repo = FakeUserRepository()
        prefs = await repo.get_preferences(user_id=42)
        assert prefs == UserPreferences()

    async def test_save_then_get_round_trip(self):
        repo = FakeUserRepository()
        prefs = UserPreferences(
            base_language="fr",
            target_language="en",
            instant_action=InstantActionType.TRANSLATE_WITH_CONTEXT,
        )
        await repo.save_preferences(user_id=1, prefs=prefs)
        retrieved = await repo.get_preferences(user_id=1)
        assert retrieved == prefs

    async def test_different_users_are_isolated(self):
        repo = FakeUserRepository()
        prefs_a = UserPreferences(base_language="fr", target_language="en")
        prefs_b = UserPreferences(base_language="en", target_language="fr")

        await repo.save_preferences(user_id=1, prefs=prefs_a)
        await repo.save_preferences(user_id=2, prefs=prefs_b)

        assert (await repo.get_preferences(user_id=1)).base_language == "fr"
        assert (await repo.get_preferences(user_id=2)).base_language == "en"

    async def test_save_overwrites_previous(self):
        repo = FakeUserRepository()
        await repo.save_preferences(
            user_id=1, prefs=UserPreferences(base_language="fr")
        )
        await repo.save_preferences(
            user_id=1, prefs=UserPreferences(base_language="en")
        )
        assert (await repo.get_preferences(user_id=1)).base_language == "en"


class TestSqliteUserRepository:
    async def test_returns_defaults_for_unknown_user(self, tmp_path):
        db = str(tmp_path / "test.db")
        repo = SqliteUserRepository(db)
        prefs = await repo.get_preferences(user_id=99)
        assert prefs == UserPreferences()

    async def test_save_then_get_round_trip(self, tmp_path):
        db = str(tmp_path / "test.db")
        repo = SqliteUserRepository(db)
        prefs = UserPreferences(
            base_language="fr",
            target_language="en",
            instant_action=InstantActionType.TRANSLATE_WITH_CONTEXT,
        )
        await repo.save_preferences(user_id=7, prefs=prefs)
        retrieved = await repo.get_preferences(user_id=7)
        assert retrieved == prefs

    async def test_survives_second_repository_instance(self, tmp_path):
        db = str(tmp_path / "test.db")
        repo1 = SqliteUserRepository(db)
        prefs = UserPreferences(base_language="fr", target_language="en")
        await repo1.save_preferences(user_id=5, prefs=prefs)

        repo2 = SqliteUserRepository(db)
        retrieved = await repo2.get_preferences(user_id=5)
        assert retrieved.base_language == "fr"
        assert retrieved.target_language == "en"

    async def test_upsert_replaces_existing_row(self, tmp_path):
        db = str(tmp_path / "test.db")
        repo = SqliteUserRepository(db)
        await repo.save_preferences(
            user_id=3, prefs=UserPreferences(base_language="fr")
        )
        await repo.save_preferences(
            user_id=3, prefs=UserPreferences(base_language="en")
        )
        assert (await repo.get_preferences(user_id=3)).base_language == "en"

    async def test_different_users_are_isolated(self, tmp_path):
        db = str(tmp_path / "test.db")
        repo = SqliteUserRepository(db)
        await repo.save_preferences(
            user_id=10, prefs=UserPreferences(base_language="fr")
        )
        await repo.save_preferences(
            user_id=11, prefs=UserPreferences(base_language="en")
        )

        assert (await repo.get_preferences(user_id=10)).base_language == "fr"
        assert (await repo.get_preferences(user_id=11)).base_language == "en"
