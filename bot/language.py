from lingua import Language, LanguageDetectorBuilder

_detector = LanguageDetectorBuilder.from_languages(
    Language.FRENCH, Language.ENGLISH
).build()


def detect_language(text: str) -> str | None:
    """Classify *text* as ``"target"`` (French) or ``"source"`` (English).

    Returns ``None`` when the detector cannot decide.
    """
    lang = _detector.detect_language_of(text)
    if lang == Language.FRENCH:
        return "target"
    if lang == Language.ENGLISH:
        return "source"
    return None
