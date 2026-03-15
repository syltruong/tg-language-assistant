"""Test the local routing module."""

from unittest.mock import patch

import pytest

from lingua import Language

from bot.config.lang import SUPPORTED_LANGUAGES
from bot.routing.local import (
    MessageHasNoTextException,
    TextHasNoWrittenContentException,
    TextTooLongException,
    UnauthorizedException,
    detect_language,
    filter_telegram_message,
)
from tests.factories import make_update


# ── filter_telegram_message ───────────────────────────────────────────


@patch("bot.routing.local._is_authorized", side_effect=lambda uid: uid == 123)
class TestFilterUnauthorized:
    @pytest.mark.parametrize("user_id", [999, 0])
    def test_unauthorized_user_raises_when_allowlist_set(self, _mock_auth, user_id):
        with pytest.raises(UnauthorizedException):
            filter_telegram_message(make_update("Hello", user_id=user_id))

    def test_authorized_user_passes_when_allowlist_set(self, _mock_auth):
        filter_telegram_message(make_update("Hello", user_id=123))


@patch("bot.routing.local._is_authorized", return_value=True)
class TestFilterNoText:
    def test_none_text_raises(self, _mock_auth):
        with pytest.raises(MessageHasNoTextException):
            filter_telegram_message(make_update(None))


@patch("bot.routing.local._is_authorized", return_value=True)
class TestFilterTooLong:
    def test_exceeds_max_length(self, _mock_auth):
        with pytest.raises(TextTooLongException):
            filter_telegram_message(make_update("a" * 501))

    def test_exactly_at_max_length_passes(self, _mock_auth):
        filter_telegram_message(make_update("a" * 500))


@patch("bot.routing.local._is_authorized", return_value=True)
class TestFilterNoWrittenContent:
    @pytest.mark.parametrize(
        "text",
        [
            "!!!???",
            "😀😂🔥",
            "123 456",
            "---___...",
            "   ",
            "🇫🇷🇬🇧",
            "$$€€¥¥",
        ],
    )
    def test_no_letters_raises(self, _mock_auth, text):
        with pytest.raises(TextHasNoWrittenContentException):
            filter_telegram_message(make_update(text))


@patch("bot.routing.local._is_authorized", return_value=True)
class TestFilterValidText:
    @pytest.mark.parametrize(
        "text",
        [
            "Hello",
            "Bonjour",
            "Hello 123!",
            "你好",
            "café ☕",
            "a",
            "Hello Bonjour Ciao",
        ],
    )
    def test_valid_text_passes(self, _mock_auth, text):
        filter_telegram_message(make_update(text))

    def test_strips_whitespace_before_length_check(self, _mock_auth):
        padded = "  " + "a" * 500 + "  "
        filter_telegram_message(make_update(padded))


# ── detect_language ──────────────────────────────────────────────────


def _supported_languages() -> list[Language]:
    """All supported languages (UI + target) for detect_language."""
    return list(SUPPORTED_LANGUAGES.keys())


class TestDetectLanguageFrench:
    @pytest.mark.parametrize(
        "text",
        [
            "Bonjour, comment allez-vous aujourd'hui ?",
            "Je voudrais un café s'il vous plaît",
            "Les enfants jouent dans le jardin",
        ],
    )
    def test_french_detected(self, text):
        assert detect_language(text, _supported_languages()) == "fr"


class TestDetectLanguageEnglish:
    @pytest.mark.parametrize(
        "text",
        [
            "Hello, how are you doing today?",
            "The weather is beautiful this morning",
            "I would like to order a coffee please",
        ],
    )
    def test_english_detected(self, text):
        assert detect_language(text, _supported_languages()) == "en"
