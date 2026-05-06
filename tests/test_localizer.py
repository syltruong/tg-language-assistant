"""Tests for the Localizer class."""

import pytest

from bot.config.messages import MsgAiError, MsgChooseAction
from bot.errors import TextTooLongError, UnauthorizedError
from bot.localizer import Localizer


class TestLocalizerResolvesStrings:
    def test_returns_string_for_known_key_and_locale(self):
        localizer = Localizer()
        result = localizer.t(MsgChooseAction, "en")
        assert result == "What can I help you with?"

    def test_defaults_to_english_when_locale_omitted(self):
        localizer = Localizer()
        assert localizer.t(MsgChooseAction) == localizer.t(MsgChooseAction, "en")

    def test_falls_back_to_english_for_unknown_locale(self):
        localizer = Localizer()
        assert localizer.t(MsgChooseAction, "xx") == localizer.t(MsgChooseAction, "en")

    def test_interpolates_kwargs_into_template(self):
        localizer = Localizer()
        result = localizer.t(MsgAiError, "en", error="timeout")
        assert result == "Error calling AI: timeout"

    def test_raises_key_error_for_unknown_key(self):
        localizer = Localizer()

        class UnknownKey:
            pass

        with pytest.raises(KeyError):
            localizer.t(UnknownKey)


class TestLocalizerAcceptsDomainErrors:
    def test_domain_error_type_resolves_as_key(self):
        localizer = Localizer()
        result = localizer.t(TextTooLongError, "en")
        assert "500" in result

    def test_unauthorized_error_type_resolves_as_key(self):
        localizer = Localizer()
        result = localizer.t(UnauthorizedError, "en")
        assert "authorized" in result.lower()
