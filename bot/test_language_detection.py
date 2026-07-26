import pytest

from bot.actions.verbs.base import LanguagePair
from bot.errors import UnsupportedLanguageError
from bot.gateway import FakeLanguageDetector, LanguageRole
from bot.language_detection import GraphLanguageClassifier
from bot.llm_interface import FakeLLMClient

EN_FR = LanguagePair(base="en", target="fr")


class _ExplodingLLMClient:
    """An LLMClient that fails the test if it's ever called."""

    async def complete(self, system_prompt, user_prompt, *, metadata=None):
        raise AssertionError("LLM fallback should not be called when the deterministic detector already matched")


class TestGraphLanguageClassifierDeterministicMatch:
    async def test_target_language_text_classified_without_llm_fallback(self):
        classifier = GraphLanguageClassifier(
            language_detector=FakeLanguageDetector("fr"),
            llm_client=_ExplodingLLMClient(),
        )

        iso, role = await classifier.classify("Bonjour", EN_FR)

        assert iso == "fr"
        assert role == LanguageRole.TARGET

    async def test_base_language_text_classified_without_llm_fallback(self):
        classifier = GraphLanguageClassifier(
            language_detector=FakeLanguageDetector("en"),
            llm_client=_ExplodingLLMClient(),
        )

        iso, role = await classifier.classify("Hello", EN_FR)

        assert iso == "en"
        assert role == LanguageRole.BASE


class TestGraphLanguageClassifierLLMFallback:
    async def test_llm_fallback_rescues_a_misdetected_target_language(self):
        classifier = GraphLanguageClassifier(
            language_detector=FakeLanguageDetector("es"),  # deterministic detector gets it wrong
            llm_client=FakeLLMClient(response="fr"),
        )

        iso, role = await classifier.classify("Bonjour", EN_FR)

        assert iso == "fr"
        assert role == LanguageRole.TARGET

    async def test_llm_fallback_still_unsupported_raises_with_base_and_target(self):
        classifier = GraphLanguageClassifier(
            language_detector=FakeLanguageDetector("es"),
            llm_client=FakeLLMClient(response="none"),
        )

        with pytest.raises(UnsupportedLanguageError) as exc_info:
            await classifier.classify("Hola", EN_FR)

        assert exc_info.value.format_kwargs == {"base": "en", "target": "fr"}
