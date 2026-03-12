"""
The first layer of processing an incoming message

1. Is it text? (eg. not image, voice, video, file etc.)
2. Does it contain any written content? Not just symbols, emojis, etc.
3. What language is it?
   a. Gibberish
   b. Among a set of languages
"""

import unicodedata

from lingua import Language, LanguageDetectorBuilder
from telegram import Message

TEXT_MAX_LENGTH = 500
SUPPORTED_LANGUAGES = [Language.FRENCH, Language.ENGLISH]
_detector = LanguageDetectorBuilder.from_languages(*SUPPORTED_LANGUAGES).build()

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

def filter_telegram_text_message(message: Message) -> str:
    """Filter out messages that don't have text."""
    text = message.text
    
    if text is None:
        raise MessageHasNoTextException()
    
    text = text.strip()
    
    if len(text) > TEXT_MAX_LENGTH:
        raise TextTooLongException()
    
    if not any(unicodedata.category(ch).startswith("L") for ch in text):
        raise TextHasNoWrittenContentException()

def detect_language(text: str, languages: list[Language]) -> Language:
    scores = [_detector.compute_language_confidence(text, language=language) for language in languages]
    return languages[scores.index(max(scores))]