"""Message Gateway — entry point to the system.

Receives a raw Telegram Update, delegates authorization, validates message text,
detects language, resolves LanguageRole, and returns a classified AnchorMessage.
"""

import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from telegram import Update

from bot.actions.verbs.base import LanguagePair
from bot.auth import Authorizer
from bot.errors import (
    MessageHasNoTextError,
    TextHasNoWrittenContentError,
    TextTooLongError,
    UnauthorizedError,
    UnsupportedLanguageError,
)

TEXT_MAX_LENGTH = 500


class LanguageRole(StrEnum):
    TARGET = "target"
    BASE = "base"


@dataclass(frozen=True)
class AnchorMessage:
    text: str
    detected_language: str
    language_role: LanguageRole


@runtime_checkable
class LanguageDetector(Protocol):
    def detect(self, text: str) -> str: ...


class FakeLanguageDetector:
    def __init__(self, iso_code: str) -> None:
        self._iso_code = iso_code

    def detect(self, text: str) -> str:
        return self._iso_code


class LinguaLanguageDetector:
    def __init__(self) -> None:
        from lingua import LanguageDetectorBuilder

        from bot.config.lang import SUPPORTED_LANGUAGES

        self._detector = LanguageDetectorBuilder.from_languages(
            *SUPPORTED_LANGUAGES.keys()
        ).build()
        self._iso_by_language = SUPPORTED_LANGUAGES

    def detect(self, text: str) -> str:
        scores = [
            (lang, self._detector.compute_language_confidence(text, language=lang))
            for lang in self._iso_by_language
        ]
        best_lang = max(scores, key=lambda x: x[1])[0]
        return self._iso_by_language[best_lang]


class MessageGateway:
    def __init__(
        self,
        authorizer: Authorizer,
        language_detector: LanguageDetector,
    ) -> None:
        self._authorizer = authorizer
        self._language_detector = language_detector

    def process(self, update: Update, language_pair: LanguagePair) -> AnchorMessage:
        user_id = update.effective_user.id if update.effective_user else None
        if not self._authorizer.is_authorized(user_id):
            raise UnauthorizedError()

        message = update.message
        if message is None or message.text is None:
            raise MessageHasNoTextError()

        text = message.text.strip()

        if len(text) > TEXT_MAX_LENGTH:
            raise TextTooLongError()

        if not any(unicodedata.category(ch).startswith("L") for ch in text):
            raise TextHasNoWrittenContentError()

        detected_iso = self._language_detector.detect(text)

        if detected_iso == language_pair.target:
            role = LanguageRole.TARGET
        elif detected_iso == language_pair.base:
            role = LanguageRole.BASE
        else:
            raise UnsupportedLanguageError()

        return AnchorMessage(
            text=text,
            detected_language=detected_iso,
            language_role=role,
        )
