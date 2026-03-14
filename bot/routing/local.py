"""
The first layer of processing an incoming message

1. Is the user authorised?
2. Is it text? (eg. not image, voice, video, file etc.)
3. Does it contain any written content? Not just symbols, emojis, etc.
4. What language is it?
   a. Gibberish
   b. Among a set of languages
"""

import unicodedata

from lingua import Language, LanguageDetectorBuilder
from telegram import Update

import os

TEXT_MAX_LENGTH = 500
SUPPORTED_UI_LANGUAGES = {
    Language.ENGLISH : "en"
}
SUPPORTED_TARGET_LANGUAGES = {
    Language.FRENCH : "fr"
}
SUPPORTED_LANGUAGES = {**SUPPORTED_UI_LANGUAGES, **SUPPORTED_TARGET_LANGUAGES}

# preferable to build the language detection once for all users
# and reuse it for all language detection operations
_detector = LanguageDetectorBuilder.from_languages(*SUPPORTED_LANGUAGES.keys()).build()

class UserFacingError(Exception):
    def __init__(self, *args, **format_kwargs):
        super().__init__(*args)
        self.format_kwargs = format_kwargs

class MessageHasNoTextException(UserFacingError):
    pass

class TextHasNoWrittenContentException(UserFacingError):
    pass

class TextTooLongException(UserFacingError):
    pass


class UnauthorizedException(UserFacingError):
    pass


def _is_authorized(user_id: int | None) -> bool:
    """Return True if the user is allowed to use the bot."""
    allowed_users = os.getenv("ALLOWED_USERS", "").split(",")
    if not allowed_users:
        return True
    return user_id in allowed_users


def filter_telegram_message(update: Update) -> None:
    """Filter out unauthorised users and messages that don't have text."""
    if not _is_authorized(update.effective_user.id if update.effective_user else None):
        raise UnauthorizedException()

    message = update.message
    if message is None or message.text is None:
        raise MessageHasNoTextException()

    text = message.text.strip()

    if len(text) > TEXT_MAX_LENGTH:
        raise TextTooLongException()

    if not any(unicodedata.category(ch).startswith("L") for ch in text):
        raise TextHasNoWrittenContentException()

def detect_language(text: str, languages: list[Language]) -> str:
    
    for lang in languages:
        assert lang in SUPPORTED_LANGUAGES, f"Language {lang} is not supported. Supported languages are {list(SUPPORTED_LANGUAGES.values())}"
    scores = [_detector.compute_language_confidence(text, language=language) for language in languages]
    
    return SUPPORTED_LANGUAGES[languages[scores.index(max(scores))]]