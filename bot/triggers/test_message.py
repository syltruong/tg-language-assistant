import pytest

from bot.actions.registry import ActionRegistry
from bot.actions.verbs.translate import TranslateAction
from bot.auth import FakeAuthorizer
from bot.gateway import FakeLanguageDetector, MessageGateway
from bot.localizer import Localizer
from bot.publisher import FakeResponsePublisher
from bot.runner import FakeActionRunner
from bot.triggers.message import MessageTrigger
from tests.factories import make_context, make_update


def _make_registry() -> ActionRegistry:
    return ActionRegistry(localizer=Localizer())


def _make_trigger(
    detected_lang: str = "fr",
    runner_result: str = "translation",
) -> tuple[MessageTrigger, FakeActionRunner, FakeResponsePublisher]:
    gateway = MessageGateway(
        authorizer=FakeAuthorizer(allow=True),
        language_detector=FakeLanguageDetector(detected_lang),
    )
    registry = _make_registry()
    runner = FakeActionRunner(result=runner_result)
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
        assert len(publisher.published) == 1
