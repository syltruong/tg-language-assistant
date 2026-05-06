import pytest

from bot.actions.registry import ActionRegistry
from bot.actions.verbs.analyze import AnalyzeAction
from bot.actions.verbs.correct import CorrectAction
from bot.localizer import Localizer
from bot.publisher import FakeResponsePublisher
from bot.runner import FakeActionRunner
from bot.triggers.keyboard import KeyboardTrigger
from bot.types import KeyboardActionType
from tests.factories import make_callback_update, make_context


def _make_registry() -> ActionRegistry:
    return ActionRegistry(localizer=Localizer())


def _make_trigger() -> tuple[KeyboardTrigger, FakeActionRunner, FakeResponsePublisher]:
    registry = _make_registry()
    runner = FakeActionRunner(result="formatted")
    publisher = FakeResponsePublisher()
    trigger = KeyboardTrigger(registry=registry, runner=runner, publisher=publisher)
    return trigger, runner, publisher


class TestKeyboardTriggerKeyboardLifecycle:
    @pytest.mark.asyncio
    async def test_reattaches_keyboard_to_original_message_after_action(self):
        from bot.keyboard import KEYBOARD

        trigger, _, publisher = _make_trigger()
        update = make_callback_update(
            callback_data=KeyboardActionType.ANALYZE,
            reply_text="Bonjour",
            message_id=77,
        )
        context = make_context()

        await trigger.handle(update, context)

        assert len(publisher.reattached) == 1
        _, message_id, markup = publisher.reattached[0]
        assert message_id == 77
        assert markup is KEYBOARD


class TestKeyboardTriggerRouting:
    @pytest.mark.asyncio
    async def test_analyze_callback_runs_analyze_action(self):
        trigger, runner, publisher = _make_trigger()
        update = make_callback_update(
            callback_data=KeyboardActionType.ANALYZE,
            reply_text="Bonjour le monde",
        )
        context = make_context()

        await trigger.handle(update, context)

        assert isinstance(runner.last_action, AnalyzeAction)
        assert len(publisher.published) == 1

    @pytest.mark.asyncio
    async def test_correct_callback_runs_correct_action(self):
        trigger, runner, _ = _make_trigger()
        update = make_callback_update(
            callback_data=KeyboardActionType.CORRECT,
            reply_text="Je veux manger",
        )
        context = make_context()

        await trigger.handle(update, context)

        assert isinstance(runner.last_action, CorrectAction)
