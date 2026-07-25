import pytest

from bot.actions.registry import ActionRegistry
from bot.actions.verbs.analyze import AnalyzeAction
from bot.actions.verbs.correct import CorrectAction
from bot.localizer import Localizer  # needed by _make_registry
from bot.publisher import FakeResponsePublisher
from bot.runner import FakeActionRunner
from bot.session import UserSession
from bot.triggers.keyboard import KeyboardTrigger
from bot.types import KeyboardActionType, Suggestion
from tests.factories import make_callback_update, make_context


def _make_registry() -> ActionRegistry:
    return ActionRegistry(localizer=Localizer())


def _make_trigger(
    runner: FakeActionRunner | None = None,
) -> tuple[KeyboardTrigger, FakeActionRunner, FakeResponsePublisher]:
    registry = _make_registry()
    runner = runner or FakeActionRunner(result="formatted")
    publisher = FakeResponsePublisher()
    trigger = KeyboardTrigger(registry=registry, runner=runner, publisher=publisher)
    return trigger, runner, publisher


class TestKeyboardTriggerKeyboardLifecycle:
    @pytest.mark.asyncio
    async def test_result_edits_slot_message(self):
        trigger, _, publisher = _make_trigger()
        update = make_callback_update(
            callback_data=KeyboardActionType.ANALYZE,
            reply_text="Bonjour",
            message_id=77,
            anchor_message_id=42,
        )
        context = make_context()

        await trigger.handle(update, context)

        _, _, slot_id, _ = publisher.edits[0]
        assert slot_id == 77

    @pytest.mark.asyncio
    async def test_stores_run_id_in_session_for_the_edited_slot(self):
        runner = FakeActionRunner(result="formatted", run_id="run-xyz")
        trigger, _, _ = _make_trigger(runner=runner)
        update = make_callback_update(
            callback_data=KeyboardActionType.ANALYZE,
            reply_text="Bonjour",
            message_id=77,
            anchor_message_id=42,
        )
        context = make_context()

        await trigger.handle(update, context)

        session = UserSession.from_context(context)
        assert session.get_run_id(77) == "run-xyz"

    @pytest.mark.asyncio
    async def test_result_carries_keyboard_markup(self):
        from bot.keyboard import build_action_keyboard

        trigger, _, publisher = _make_trigger()
        update = make_callback_update(
            callback_data=KeyboardActionType.ANALYZE,
            reply_text="Bonjour",
        )
        context = make_context()

        await trigger.handle(update, context)

        _, _, _, reply_markup = publisher.edits[0]
        assert reply_markup.inline_keyboard == build_action_keyboard().inline_keyboard


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
        assert len(publisher.edits) == 1

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


_SUGGESTIONS = [
    Suggestion(text="Bien merci!", note="warm"),
    Suggestion(text="Oui, ça va!", note="playful"),
]


class TestKeyboardTriggerReplyFlow:
    @pytest.mark.asyncio
    async def test_reply_callback_stores_suggestions_in_session(self):
        runner = FakeActionRunner(result="• Bien merci!", suggestions=_SUGGESTIONS)
        trigger, _, _ = _make_trigger(runner=runner)
        update = make_callback_update(
            callback_data=KeyboardActionType.REPLY,
            reply_text="Ça va?",
            message_id=77,
            anchor_message_id=42,
        )
        context = make_context()

        await trigger.handle(update, context)

        session = UserSession.from_context(context)
        assert session.get_suggestions(77) == _SUGGESTIONS

    @pytest.mark.asyncio
    async def test_reply_callback_attaches_suggestions_keyboard(self):
        from bot.keyboard import build_action_keyboard

        runner = FakeActionRunner(result="• Bien merci!", suggestions=_SUGGESTIONS)
        trigger, _, publisher = _make_trigger(runner=runner)
        update = make_callback_update(
            callback_data=KeyboardActionType.REPLY,
            reply_text="Ça va?",
            message_id=77,
        )
        context = make_context()

        await trigger.handle(update, context)

        _, _, _, reply_markup = publisher.edits[0]
        assert reply_markup.inline_keyboard != build_action_keyboard().inline_keyboard
        assert len(reply_markup.inline_keyboard) == 4
        assert reply_markup.inline_keyboard[0][0].callback_data == "select:0"


class TestKeyboardTriggerRephraseFlow:
    @pytest.mark.asyncio
    async def test_rephrase_callback_stores_suggestions_in_session(self):
        runner = FakeActionRunner(result="• C'est super!", suggestions=_SUGGESTIONS)
        trigger, _, _ = _make_trigger(runner=runner)
        update = make_callback_update(
            callback_data=KeyboardActionType.REPHRASE,
            reply_text="C'est bon",
            message_id=77,
            anchor_message_id=42,
        )
        context = make_context()

        await trigger.handle(update, context)

        session = UserSession.from_context(context)
        assert session.get_suggestions(77) == _SUGGESTIONS

    @pytest.mark.asyncio
    async def test_rephrase_callback_attaches_suggestions_keyboard(self):
        from bot.keyboard import build_action_keyboard

        runner = FakeActionRunner(result="• C'est super!", suggestions=_SUGGESTIONS)
        trigger, _, publisher = _make_trigger(runner=runner)
        update = make_callback_update(
            callback_data=KeyboardActionType.REPHRASE,
            reply_text="C'est bon",
            message_id=77,
        )
        context = make_context()

        await trigger.handle(update, context)

        _, _, _, reply_markup = publisher.edits[0]
        assert reply_markup.inline_keyboard != build_action_keyboard().inline_keyboard
        assert len(reply_markup.inline_keyboard) == 4
        assert reply_markup.inline_keyboard[0][0].callback_data == "select:0"


class TestKeyboardTriggerSelectionFlow:
    @pytest.mark.asyncio
    async def test_select_callback_edits_slot_with_selected_text_and_standard_keyboard(self):
        from bot.keyboard import build_action_keyboard

        trigger, _, publisher = _make_trigger()
        update = make_callback_update(
            callback_data="select:1",
            reply_text="Ça va?",
            message_id=77,
            anchor_message_id=42,
        )
        context = make_context(user_data={
            "suggestions": {77: _SUGGESTIONS},
        })

        await trigger.handle(update, context)

        result, _, slot_id, reply_markup = publisher.edits[0]
        assert result.text == "Oui, ça va!"
        assert slot_id == 77
        assert reply_markup.inline_keyboard == build_action_keyboard().inline_keyboard
