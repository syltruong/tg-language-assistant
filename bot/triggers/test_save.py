import pytest

from bot.config.messages import MsgSaved, MsgSaveFailed, t
from bot.insights import InMemoryInsightRepository
from bot.keyboard import SAVE, build_action_keyboard
from bot.triggers.save import SaveTrigger
from tests.factories import make_callback_update, make_context


def _make_update(message_id: int = 77, anchor: str = "Bonjour", slot: str = "a casual greeting"):
    update = make_callback_update(
        callback_data=SAVE,
        message_id=message_id,
        reply_text=anchor,
        slot_text=slot,
    )
    update.callback_query.message.reply_markup = build_action_keyboard()
    return update


class TestKeepingATurn:
    @pytest.mark.asyncio
    async def test_tapping_save_keeps_the_anchor_and_the_result_on_screen(self):
        repository = InMemoryInsightRepository()
        trigger = SaveTrigger(repository=repository)
        context = make_context()

        await trigger.handle(_make_update(), context)

        kept = await repository.list_for_user(user_id=123)
        assert [insight.anchor_text for insight in kept] == ["Bonjour"]
        assert kept[0].result_text == "a casual greeting"

    @pytest.mark.asyncio
    async def test_keeps_the_turn_even_when_the_session_is_gone(self):
        """The property that distinguishes Save from Rating and Suggestion selection.

        Both of those silently no-op on a lost Session — acceptable when the cost
        is one lost tap. Here the user believes they kept something, so capture
        reads everything it needs off the callback instead.
        """
        repository = InMemoryInsightRepository()
        trigger = SaveTrigger(repository=repository)
        context = make_context()  # empty user_data, as after a restart

        await trigger.handle(_make_update(), context)

        kept = await repository.list_for_user(user_id=123)
        assert len(kept) == 1
        assert kept[0].anchor_text == "Bonjour"
        assert kept[0].run_id is None

    @pytest.mark.asyncio
    async def test_records_which_action_rendered_the_slot(self):
        repository = InMemoryInsightRepository()
        trigger = SaveTrigger(repository=repository)
        context = make_context(user_data={"slot_actions": {77: "correct"}})

        await trigger.handle(_make_update(message_id=77), context)

        kept = await repository.list_for_user(user_id=123)
        assert kept[0].action_type == "correct"

    @pytest.mark.asyncio
    async def test_records_an_unknown_action_when_the_session_cannot_say(self):
        repository = InMemoryInsightRepository()
        trigger = SaveTrigger(repository=repository)

        await trigger.handle(_make_update(), make_context())

        kept = await repository.list_for_user(user_id=123)
        assert kept[0].action_type == "unknown"


class TestSaveFeedbackToTheUser:
    @pytest.mark.asyncio
    async def test_the_button_flips_to_saved(self):
        repository = InMemoryInsightRepository()
        trigger = SaveTrigger(repository=repository)
        update = _make_update()

        await trigger.handle(update, make_context())

        markup = update.callback_query.edit_message_reply_markup.call_args.kwargs["reply_markup"]
        assert markup.inline_keyboard[-3][0].text == t(MsgSaved)

    @pytest.mark.asyncio
    async def test_a_second_tap_does_not_keep_the_turn_twice(self):
        repository = InMemoryInsightRepository()
        trigger = SaveTrigger(repository=repository)
        context = make_context()

        await trigger.handle(_make_update(), context)
        await trigger.handle(_make_update(), context)

        assert len(await repository.list_for_user(user_id=123)) == 1

    @pytest.mark.asyncio
    async def test_a_failing_repository_tells_the_user_instead_of_raising(self):
        class FailingRepository:
            async def save(self, insight):
                raise RuntimeError("disk full")

            async def list_for_user(self, user_id, limit=20):
                return []

        trigger = SaveTrigger(repository=FailingRepository())
        update = _make_update()

        await trigger.handle(update, make_context())

        update.callback_query.answer.assert_called_once_with(t(MsgSaveFailed))
        update.callback_query.edit_message_reply_markup.assert_not_called()
