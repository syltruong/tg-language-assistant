"""Language configuration: supported languages and display names."""

from lingua import Language

SUPPORTED_UI_LANGUAGES = {Language.ENGLISH: "en"}
SUPPORTED_TARGET_LANGUAGES = {Language.FRENCH: "fr", Language.MALAY: "ms", Language.CHINESE: "zh"}
SUPPORTED_LANGUAGES = {**SUPPORTED_UI_LANGUAGES, **SUPPORTED_TARGET_LANGUAGES}

LANGUAGE_NAMES: dict[str, str] = {
    code: lang.name.title() for lang, code in SUPPORTED_LANGUAGES.items()
}

LANGUAGE_FLAGS: dict[str, str] = {
    "en": "🇬🇧",
    "fr": "🇫🇷",
    "ms": "🇲🇾",
    "zh": "🇨🇳",
}

LANGUAGE_DISPLAY_NAMES: dict[str, str] = {
    "ms": "Bahasa Melayu",
    "zh": "Mandarin Chinese",
}
