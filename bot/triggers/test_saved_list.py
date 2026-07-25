import pytest

from bot.config.messages import MsgSavedListEmpty, t
from bot.insights import InMemoryInsightRepository, SavedInsight
from bot.localizer import Localizer
from bot.triggers.saved_list import SavedListTrigger
from tests.factories import make_context, make_update


def an_insight(**overrides) -> SavedInsight:
    defaults = dict(
        user_id=123,
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


def _sent_text(update) -> str:
    return update.message.reply_text.call_args.args[0]


class TestSavedList:
    @pytest.mark.asyncio
    async def test_lists_kept_insights_most_recent_first(self):
        repository = InMemoryInsightRepository()
        await repository.save(an_insight(slot_message_id=1, anchor_text="older"))
        await repository.save(an_insight(slot_message_id=2, anchor_text="newer"))
        trigger = SavedListTrigger(repository=repository, localizer=Localizer())
        update = make_update()

        await trigger.handle(update, make_context())

        text = _sent_text(update)
        assert text.index("newer") < text.index("older")

    @pytest.mark.asyncio
    async def test_shows_which_action_produced_each_insight(self):
        repository = InMemoryInsightRepository()
        await repository.save(an_insight(action_type="correct"))
        trigger = SavedListTrigger(repository=repository, localizer=Localizer())
        update = make_update()

        await trigger.handle(update, make_context())

        assert "correct" in _sent_text(update)

    @pytest.mark.asyncio
    async def test_says_so_when_nothing_has_been_kept(self):
        trigger = SavedListTrigger(
            repository=InMemoryInsightRepository(), localizer=Localizer()
        )
        update = make_update()

        await trigger.handle(update, make_context())

        assert _sent_text(update) == t(MsgSavedListEmpty)

    @pytest.mark.asyncio
    async def test_lists_only_the_requesting_users_insights(self):
        repository = InMemoryInsightRepository()
        await repository.save(an_insight(user_id=123, anchor_text="mine"))
        await repository.save(an_insight(user_id=999, anchor_text="theirs"))
        trigger = SavedListTrigger(repository=repository, localizer=Localizer())
        update = make_update(user_id=123)

        await trigger.handle(update, make_context())

        text = _sent_text(update)
        assert "mine" in text
        assert "theirs" not in text
