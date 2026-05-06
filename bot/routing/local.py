"""
The first layer of processing an incoming message

1. Is the user authorised?
2. Is it text? (eg. not image, voice, video, file etc.)
3. Does it contain any written content? Not just symbols, emojis, etc.
4. What language is it?
   a. Gibberish
   b. Among a set of languages
"""

import os
import unicodedata

from lingua import Language, LanguageDetectorBuilder
from telegram import Update

from bot.config.lang import SUPPORTED_LANGUAGES
from bot.errors import (
    MessageHasNoTextError,
    TextHasNoWrittenContentError,
    TextTooLongError,
    UnauthorizedError,
)

TEXT_MAX_LENGTH = 500

# preferable to build the language detection once for all users
# and reuse it for all language detection operations
_detector = LanguageDetectorBuilder.from_languages(*SUPPORTED_LANGUAGES.keys()).build()


def _is_authorized(user_id: int | None) -> bool:
    """Return True if the user is allowed to use the bot.

    When ALLOWED_USERS is empty or unset, all users are allowed (no whitelist).
    """
    raw = os.getenv("ALLOWED_USERS", "").strip()
    if not raw:
        return True
    allowed = {int(uid.strip()) for uid in raw.split(",") if uid.strip()}
    if not allowed:
        return True
    return user_id in allowed


def filter_telegram_message(update: Update) -> None:
    """Filter out unauthorised users and messages that don't have text."""
    if not _is_authorized(update.effective_user.id if update.effective_user else None):
        raise UnauthorizedError()

    message = update.message
    if message is None or message.text is None:
        raise MessageHasNoTextError()

    text = message.text.strip()

    if len(text) > TEXT_MAX_LENGTH:
        raise TextTooLongError()

    if not any(unicodedata.category(ch).startswith("L") for ch in text):
        raise TextHasNoWrittenContentError()


def detect_language(text: str, languages: list[Language]) -> str:

    for lang in languages:
        assert lang in SUPPORTED_LANGUAGES, (
            f"Language {lang} is not supported. "
            f"Supported: {list(SUPPORTED_LANGUAGES.values())}"
        )
    scores = [
        _detector.compute_language_confidence(text, language=language)
        for language in languages
    ]

    return SUPPORTED_LANGUAGES[languages[scores.index(max(scores))]]
