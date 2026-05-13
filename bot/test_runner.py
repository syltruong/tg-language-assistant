import json

import pytest

from bot.actions.verbs.analyze import AnalyzeAction
from bot.actions.verbs.base import LanguagePair
from bot.actions.verbs.rephrase import RephraseAction
from bot.actions.verbs.reply import ReplyAction
from bot.actions.verbs.translate import TranslateAction
from bot.gateway import AnchorMessage, LanguageRole
from bot.llm_interface import FakeLLMClient
from bot.localizer import Localizer
from bot.runner import ActionRunner
from bot.types import FormattedResult, Suggestion

EN_FR = LanguagePair(base="en", target="fr")
_TRANSLATE_TEMPLATE = "Translate {text} from {from_language} to {to_language}."
_SYSTEM_TEMPLATE = "You help {base_language} speakers learn {target_language}."


def _make_runner(response: str) -> ActionRunner:
    return ActionRunner(
        llm=FakeLLMClient(response=response),
        system_prompt_template=_SYSTEM_TEMPLATE,
    )


class _SequenceFakeLLMClient:
    """Returns responses in sequence; repeats the last one when exhausted."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self._index = 0

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        response = self._responses[min(self._index, len(self._responses) - 1)]
        self._index += 1
        return response


def _make_sequence_runner(responses: list[str]) -> ActionRunner:
    return ActionRunner(
        llm=_SequenceFakeLLMClient(responses),
        system_prompt_template=_SYSTEM_TEMPLATE,
    )


def _make_translate_action() -> TranslateAction:
    return TranslateAction(
        localizer=Localizer(),
        prompt_template=_TRANSLATE_TEMPLATE,
    )


_ANALYZE_TEMPLATE = "Analyze {text} in {target_language} for a {base_language} speaker."


def _make_analyze_action() -> AnalyzeAction:
    return AnalyzeAction(
        localizer=Localizer(),
        prompt_template=_ANALYZE_TEMPLATE,
    )


_VALID_ANALYZE_JSON = json.dumps(
    {
        "vocabulary": [{"form_in_text": "bonjour", "translation": "hello"}],
        "grammar": [],
    }
)


class TestActionRunnerStructuredJson:
    @pytest.mark.asyncio
    async def test_retries_on_malformed_json_and_succeeds_on_valid_response(self):
        runner = _make_sequence_runner(
            ["not-json", "also-not-json", _VALID_ANALYZE_JSON]
        )
        action = _make_analyze_action()
        anchor = AnchorMessage(
            text="Bonjour", detected_language="fr", language_role=LanguageRole.TARGET
        )

        result = await runner.run(action, anchor, EN_FR)

        assert "bonjour" in result.text

    @pytest.mark.asyncio
    async def test_raises_after_max_retries_exhausted(self):
        runner = _make_sequence_runner(["not-json", "not-json", "not-json"])
        action = _make_analyze_action()
        anchor = AnchorMessage(
            text="Bonjour", detected_language="fr", language_role=LanguageRole.TARGET
        )

        with pytest.raises(ValueError):
            await runner.run(action, anchor, EN_FR)

    @pytest.mark.asyncio
    async def test_structured_json_action_returns_formatted_result(self):
        runner = _make_runner(_VALID_ANALYZE_JSON)
        action = _make_analyze_action()
        anchor = AnchorMessage(
            text="Bonjour", detected_language="fr", language_role=LanguageRole.TARGET
        )

        result = await runner.run(action, anchor, EN_FR)

        assert isinstance(result, FormattedResult)
        assert "bonjour" in result.text
        assert "hello" in result.text
        assert result.parse_mode == "HTML"


class TestActionRunnerPlainText:
    @pytest.mark.asyncio
    async def test_plain_text_action_returns_formatted_result(self):
        runner = _make_runner("Bonjour")
        action = _make_translate_action()
        anchor = AnchorMessage(
            text="Hello", detected_language="en", language_role=LanguageRole.BASE
        )

        result = await runner.run(action, anchor, EN_FR)

        assert isinstance(result, FormattedResult)
        assert result.text == "Bonjour"
        assert result.parse_mode is None


_REPLY_TEMPLATE = "Generate {n} replies to {text} in {target_language}."
_VALID_REPLY_JSON = json.dumps([
    {"text": "Bien merci!", "note": "warm"},
    {"text": "Oui, ça va!", "note": "playful"},
])

_REPHRASE_TEMPLATE = "Rephrase {text} in {target_language} in 3 ways."
_VALID_REPHRASE_JSON = json.dumps([
    {"text": "C'est super!", "note": "casual"},
    {"text": "C'est excellent!", "note": "formal"},
])


def _make_reply_action() -> ReplyAction:
    return ReplyAction(localizer=Localizer(), prompt_template=_REPLY_TEMPLATE)


def _make_rephrase_action() -> RephraseAction:
    return RephraseAction(localizer=Localizer(), prompt_template=_REPHRASE_TEMPLATE)


class TestActionRunnerReplyAction:
    @pytest.mark.asyncio
    async def test_reply_action_populates_suggestions_in_result(self):
        runner = _make_runner(_VALID_REPLY_JSON)
        action = _make_reply_action()
        anchor = AnchorMessage(
            text="Ça va?", detected_language="fr", language_role=LanguageRole.TARGET
        )

        result = await runner.run(action, anchor, EN_FR)

        assert result.suggestions == [
            Suggestion(text="Bien merci!", note="warm"),
            Suggestion(text="Oui, ça va!", note="playful"),
        ]

    @pytest.mark.asyncio
    async def test_non_reply_action_has_no_suggestions(self):
        runner = _make_runner("Bonjour")
        action = _make_translate_action()
        anchor = AnchorMessage(
            text="Hello", detected_language="en", language_role=LanguageRole.BASE
        )

        result = await runner.run(action, anchor, EN_FR)

        assert result.suggestions is None


class TestActionRunnerRephraseAction:
    @pytest.mark.asyncio
    async def test_rephrase_action_populates_suggestions_in_result(self):
        runner = _make_runner(_VALID_REPHRASE_JSON)
        action = _make_rephrase_action()
        anchor = AnchorMessage(
            text="C'est bon", detected_language="fr", language_role=LanguageRole.TARGET
        )

        result = await runner.run(action, anchor, EN_FR)

        assert result.suggestions == [
            Suggestion(text="C'est super!", note="casual"),
            Suggestion(text="C'est excellent!", note="formal"),
        ]
