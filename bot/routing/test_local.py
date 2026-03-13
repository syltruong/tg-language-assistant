"""Test the local routing module."""
from unittest.mock import MagicMock

import pytest

from lingua import Language

from bot.routing.local import (
    MessageHasNoTextException,
    SUPPORTED_LANGUAGES,
    TextHasNoWrittenContentException,
    TextTooLongException,
    detect_language,
    filter_telegram_text_message,
)

def _make_message(text: str | None) -> MagicMock:
    msg = MagicMock()
    msg.text = text
    return msg


# ── filter_telegram_text_message ─────────────────────────────────────


class TestFilterNoText:
    def test_none_text_raises(self):
        with pytest.raises(MessageHasNoTextException):
            filter_telegram_text_message(_make_message(None))


class TestFilterTooLong:
    def test_exceeds_max_length(self):
        with pytest.raises(TextTooLongException):
            filter_telegram_text_message(_make_message("a" * 501))

    def test_exactly_at_max_length_passes(self):
        filter_telegram_text_message(_make_message("a" * 500))


class TestFilterNoWrittenContent:
    @pytest.mark.parametrize("text", [
        "!!!???",
        "😀😂🔥",
        "123 456",
        "---___...",
        "   ",
        "🇫🇷🇬🇧",
        "$$€€¥¥",
    ])
    def test_no_letters_raises(self, text):
        with pytest.raises(TextHasNoWrittenContentException):
            filter_telegram_text_message(_make_message(text))


class TestFilterValidText:
    @pytest.mark.parametrize("text", [
        "Hello",
        "Bonjour",
        "Hello 123!",
        "你好",
        "café ☕",
        "a",
        "Hello Bonjour Ciao",
    ])
    def test_valid_text_passes(self, text):
        filter_telegram_text_message(_make_message(text))

    def test_strips_whitespace_before_length_check(self):
        padded = "  " + "a" * 500 + "  "
        filter_telegram_text_message(_make_message(padded))


# ── detect_language ──────────────────────────────────────────────────


def _supported_languages() -> list[Language]:
    """All supported languages (UI + target) for detect_language."""
    return list(SUPPORTED_LANGUAGES.keys())


class TestDetectLanguageFrench:
    @pytest.mark.parametrize("text", [
        "Bonjour, comment allez-vous aujourd'hui ?",
        "Je voudrais un café s'il vous plaît",
        "Les enfants jouent dans le jardin",
    ])
    def test_french_detected(self, text):
        assert detect_language(text, _supported_languages()) == "fr"


class TestDetectLanguageEnglish:
    @pytest.mark.parametrize("text", [
        "Hello, how are you doing today?",
        "The weather is beautiful this morning",
        "I would like to order a coffee please",
    ])
    def test_english_detected(self, text):
        assert detect_language(text, _supported_languages()) == "en"
