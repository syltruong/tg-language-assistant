import pytest

from bot.actions.verbs.base import LanguagePair
from bot.auth import FakeAuthorizer
from bot.errors import (
    MessageHasNoTextError,
    TextHasNoWrittenContentError,
    TextTooLongError,
    UnauthorizedError,
    UnsupportedLanguageError,
)
from bot.gateway import (
    TEXT_MAX_LENGTH,
    AnchorMessage,
    LanguageRole,
    MessageGateway,
)
from bot.language_detection import FakeLanguageClassifier
from tests.factories import make_update

EN_FR = LanguagePair(base="en", target="fr")


class _RaisingClassifier:
    """A language classifier that always reports the language as unsupported."""

    async def classify(self, text, language_pair):
        raise UnsupportedLanguageError(base=language_pair.base, target=language_pair.target)


class TestMessageGatewayRejections:
    async def test_language_not_in_pair_raises(self):
        gw = MessageGateway(
            authorizer=FakeAuthorizer(allow=True),
            language_classifier=_RaisingClassifier(),
        )
        update = make_update(text="Hola mundo", user_id=1)

        with pytest.raises(UnsupportedLanguageError):
            await gw.process(update, EN_FR)

    async def test_text_with_no_written_content_raises(self):
        gw = MessageGateway(
            authorizer=FakeAuthorizer(allow=True),
            language_classifier=FakeLanguageClassifier("fr", LanguageRole.TARGET),
        )
        update = make_update(text="😀🎉🔥", user_id=1)

        with pytest.raises(TextHasNoWrittenContentError):
            await gw.process(update, EN_FR)

    async def test_text_too_long_raises(self):
        gw = MessageGateway(
            authorizer=FakeAuthorizer(allow=True),
            language_classifier=FakeLanguageClassifier("fr", LanguageRole.TARGET),
        )
        update = make_update(text="a" * (TEXT_MAX_LENGTH + 1), user_id=1)

        with pytest.raises(TextTooLongError):
            await gw.process(update, EN_FR)

    async def test_message_with_no_text_raises(self):
        gw = MessageGateway(
            authorizer=FakeAuthorizer(allow=True),
            language_classifier=FakeLanguageClassifier("fr", LanguageRole.TARGET),
        )
        update = make_update(text=None, user_id=1)

        with pytest.raises(MessageHasNoTextError):
            await gw.process(update, EN_FR)

    async def test_unauthorized_user_raises(self):
        gw = MessageGateway(
            authorizer=FakeAuthorizer(allow=False),
            language_classifier=FakeLanguageClassifier("fr", LanguageRole.TARGET),
        )
        update = make_update(text="Bonjour", user_id=999)

        with pytest.raises(UnauthorizedError):
            await gw.process(update, EN_FR)


class TestMessageGatewayHappyPath:
    async def test_text_is_stripped_in_returned_anchor(self):
        gw = MessageGateway(
            authorizer=FakeAuthorizer(allow=True),
            language_classifier=FakeLanguageClassifier("fr", LanguageRole.TARGET),
        )
        update = make_update(text="  Bonjour  ", user_id=1)

        result = await gw.process(update, EN_FR)

        assert result.text == "Bonjour"

    async def test_base_language_message_returns_anchor_with_base_role(self):
        gw = MessageGateway(
            authorizer=FakeAuthorizer(allow=True),
            language_classifier=FakeLanguageClassifier("en", LanguageRole.BASE),
        )
        update = make_update(text="Hello", user_id=1)

        result = await gw.process(update, EN_FR)

        assert result == AnchorMessage(
            text="Hello",
            detected_language="en",
            language_role=LanguageRole.BASE,
        )

    async def test_target_language_message_returns_anchor_with_target_role(self):
        gw = MessageGateway(
            authorizer=FakeAuthorizer(allow=True),
            language_classifier=FakeLanguageClassifier("fr", LanguageRole.TARGET),
        )
        update = make_update(text="Bonjour", user_id=1)

        result = await gw.process(update, EN_FR)

        assert result == AnchorMessage(
            text="Bonjour",
            detected_language="fr",
            language_role=LanguageRole.TARGET,
        )
