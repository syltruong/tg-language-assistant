import pytest

from bot.actions.registry import ActionRegistry
from bot.actions.verbs.translate import TranslateAction
from bot.auth import FakeAuthorizer
from bot.gateway import FakeLanguageDetector, MessageGateway
from bot.localizer import Localizer
from bot.publisher import FakeResponsePublisher
from bot.runner import FakeActionRunner
from bot.session import UserSession
from bot.triggers.message import MessageTrigger
from tests.factories import make_context, make_update


def _make_registry() -> ActionRegistry:
    return ActionRegistry(localizer=Localizer())


def _make_trigger(
    detected_lang: str = "fr",
    runner_result: str = "translation",
    runner_run_id: str | None = None,
) -> tuple[MessageTrigger, FakeActionRunner, FakeResponsePublisher]:
    gateway = MessageGateway(
        authorizer=FakeAuthorizer(allow=True),
        language_detector=FakeLanguageDetector(detected_lang),
    )
    registry = _make_registry()
    runner = FakeActionRunner(result=runner_result, run_id=runner_run_id)
    publisher = FakeResponsePublisher()
    trigger = MessageTrigger(
        gateway=gateway,
        registry=registry,
        runner=runner,
        publisher=publisher,
    )
    return trigger, runner, publisher


class TestMessageTriggerRouting:
    @pytest.mark.asyncio
    async def test_base_language_message_also_runs_translate_action(self):
        trigger, runner, _ = _make_trigger(detected_lang="en")
        update = make_update(text="Hello", user_id=1)
        context = make_context()

        await trigger.handle(update, context)

        assert isinstance(runner.last_action, TranslateAction)
        assert runner.last_anchor.detected_language == "en"

    @pytest.mark.asyncio
    async def test_target_language_message_runs_translate_action(self):
        trigger, runner, publisher = _make_trigger(detected_lang="fr")
        update = make_update(text="Bonjour", user_id=1)
        context = make_context()

        await trigger.handle(update, context)

        assert isinstance(runner.last_action, TranslateAction)
        assert len(publisher.new_slots_published) == 1

    @pytest.mark.asyncio
    async def test_stores_run_id_in_session_for_the_published_message(self):
        trigger, _, _ = _make_trigger(detected_lang="fr", runner_run_id="run-abc")
        update = make_update(text="Bonjour", user_id=1)
        context = make_context()

        await trigger.handle(update, context)

        session = UserSession.from_context(context)
        # FakeResponsePublisher assigns ids to the messages it sends, starting at 1000.
        assert session.get_run_id(1000) == "run-abc"
