"""Tests for the locale-aware UI string catalog."""

import pytest

from bot.config.messages import (
    CATALOGS,
    DEFAULT_LOCALE,
    MsgAiError,
    MsgChooseAction,
    MsgThinking,
    t,
)
from bot.routing.local import TextTooLongException


class TestTranslateFunction:
    def test_returns_english_string_for_default_locale(self):
        result = t(MsgChooseAction)
        assert result == CATALOGS["en"][MsgChooseAction]

    def test_returns_english_string_with_explicit_locale(self):
        result = t(MsgThinking, "en")
        assert result == CATALOGS["en"][MsgThinking]

    def test_falls_back_to_english_for_unknown_locale(self):
        result = t(MsgChooseAction, "xx")
        assert result == CATALOGS["en"][MsgChooseAction]

    def test_resolves_exception_class_key(self):
        result = t(TextTooLongException)
        assert result == CATALOGS["en"][TextTooLongException]

    def test_format_kwargs_are_interpolated(self):
        result = t(MsgAiError, "en", error="timeout")
        assert result == "Error calling AI: timeout"

    def test_missing_key_raises_key_error(self):
        class UnknownKey:
            pass

        with pytest.raises(KeyError):
            t(UnknownKey)


class TestCatalogCompleteness:
    def test_all_locales_have_same_keys_as_english(self):
        en_keys = set(CATALOGS["en"].keys())
        for locale, catalog in CATALOGS.items():
            if locale == DEFAULT_LOCALE:
                continue
            missing = en_keys - set(catalog.keys())
            assert not missing, (
                f"Locale '{locale}' is missing keys: {missing}"
            )
