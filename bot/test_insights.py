"""Behavioural contract for the Insight Repository.

Every test runs against both implementations. The fake is what PR 3's trigger
tests depend on, so it has to behave like the real one or those tests lie.
"""

import pytest

from bot.insights import (
    InMemoryInsightRepository,
    InsightRepositoryProtocol,
    SavedInsight,
    SqliteInsightRepository,
)
from bot.storage.db import Database


def an_insight(**overrides) -> SavedInsight:
    defaults = dict(
        user_id=1,
        chat_id=2,
        slot_message_id=3,
        anchor_text="bonjour",
        detected_language="fr",
        base_language="en",
        target_language="fr",
        action_type="analyze",
        result_text="a casual greeting",
    )
    return SavedInsight(**{**defaults, **overrides})


@pytest.fixture(params=["sqlite", "in_memory"])
async def repository(request, tmp_path):
    if request.param == "in_memory":
        yield InMemoryInsightRepository()
        return

    database = Database(path=tmp_path / "bot.db")
    await database.connect()
    yield SqliteInsightRepository(database=database)
    await database.close()


class TestSavingInsights:
    async def test_a_saved_insight_can_be_read_back(self, repository):
        await repository.save(an_insight(anchor_text="bonjour"))

        stored = await repository.list_for_user(user_id=1)

        assert [insight.anchor_text for insight in stored] == ["bonjour"]

    async def test_keeping_the_same_turn_and_action_twice_stores_one_insight(self, repository):
        """Double-tapping Save on the same view is a no-op, not a duplicate."""
        first = await repository.save(an_insight(action_type="analyze"))

        second = await repository.save(an_insight(action_type="analyze"))

        assert first is not None
        assert second is None
        assert len(await repository.list_for_user(user_id=1)) == 1

    async def test_the_same_turn_kept_under_two_actions_stores_both(self, repository):
        """Analyze then Correct on one turn are two different lessons."""
        await repository.save(an_insight(action_type="analyze"))
        await repository.save(an_insight(action_type="correct"))

        stored = await repository.list_for_user(user_id=1)

        assert {insight.action_type for insight in stored} == {"analyze", "correct"}


class TestListingInsights:
    async def test_lists_most_recently_kept_first(self, repository):
        await repository.save(an_insight(slot_message_id=1, anchor_text="older"))
        await repository.save(an_insight(slot_message_id=2, anchor_text="newer"))

        stored = await repository.list_for_user(user_id=1)

        assert [insight.anchor_text for insight in stored] == ["newer", "older"]

    async def test_lists_only_the_requesting_users_insights(self, repository):
        await repository.save(an_insight(user_id=1, anchor_text="mine"))
        await repository.save(an_insight(user_id=2, anchor_text="theirs"))

        stored = await repository.list_for_user(user_id=1)

        assert [insight.anchor_text for insight in stored] == ["mine"]

    async def test_honours_the_limit(self, repository):
        for slot in range(5):
            await repository.save(an_insight(slot_message_id=slot))

        stored = await repository.list_for_user(user_id=1, limit=2)

        assert len(stored) == 2

    async def test_round_trips_every_field(self, repository):
        await repository.save(
            an_insight(
                anchor_text="je suis allé",
                detected_language="fr",
                base_language="en",
                target_language="fr",
                action_type="correct",
                result_text="<b>allé</b> agrees with the subject",
                parse_mode="HTML",
                run_id="run-abc",
            )
        )

        kept = (await repository.list_for_user(user_id=1))[0]

        assert kept.anchor_text == "je suis allé"
        assert kept.result_text == "<b>allé</b> agrees with the subject"
        assert kept.parse_mode == "HTML"
        assert kept.run_id == "run-abc"
        assert kept.created_at is not None
        assert kept.id is not None

    async def test_a_run_id_is_optional(self, repository):
        """Session may be gone by the time Save is tapped — capture must not depend on it."""
        await repository.save(an_insight(run_id=None))

        kept = (await repository.list_for_user(user_id=1))[0]

        assert kept.run_id is None


class TestSoftDeletion:
    """No delete UI ships yet, but the read path must already respect the column."""

    async def test_soft_deleted_insights_are_not_listed(self, tmp_path):
        database = Database(path=tmp_path / "bot.db")
        await database.connect()
        repository = SqliteInsightRepository(database=database)
        await repository.save(an_insight())

        await database.connection.execute(
            "UPDATE saved_insights SET deleted_at = '2026-07-25T00:00:00Z'"
        )
        await database.connection.commit()

        assert await repository.list_for_user(user_id=1) == []

        await database.close()


class TestProtocolConformance:
    def test_sqlite_repository_satisfies_the_protocol(self):
        assert isinstance(
            SqliteInsightRepository(database=Database(path="unused.db")),
            InsightRepositoryProtocol,
        )

    def test_in_memory_repository_satisfies_the_protocol(self):
        assert isinstance(InMemoryInsightRepository(), InsightRepositoryProtocol)
