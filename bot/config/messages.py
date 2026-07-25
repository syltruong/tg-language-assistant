"""Locale-aware UI string catalog.

Exception classes and ``MsgKey`` subclasses serve as dictionary keys.
Call ``t(key, locale)`` to resolve the user-facing string.
"""

from __future__ import annotations

from bot.errors import (
    MessageHasNoTextError,
    TextHasNoWrittenContentError,
    TextTooLongError,
    UnauthorizedError,
)

DEFAULT_LOCALE = "en"


# ── Non-error UI string keys ─────────────────────────────────────────


class MsgKey:
    """Base class for non-error UI string keys."""


class MsgChooseAction(MsgKey):
    pass


class MsgClear(MsgKey):
    pass


class MsgThinking(MsgKey):
    pass


class MsgNoContent(MsgKey):
    pass


class MsgExpired(MsgKey):
    pass


class MsgUnknownAction(MsgKey):
    pass


class MsgNoMessage(MsgKey):
    pass


class MsgUnauthorized(MsgKey):
    pass


class MsgAiError(MsgKey):
    pass


class MsgTooLong(MsgKey):
    pass


class MsgUnknownLanguage(MsgKey):
    pass


class MsgWantToGoDeeper(MsgKey):
    pass


class MsgNoReplyText(MsgKey):
    pass


class MsgNoCorrectionsNeeded(MsgKey):
    pass


class MsgChooseLanguage(MsgKey):
    pass


class MsgLanguageSelected(MsgKey):
    pass


class MsgRateThisResponse(MsgKey):
    pass


class MsgSave(MsgKey):
    pass


class MsgSaved(MsgKey):
    pass


class MsgSaveFailed(MsgKey):
    pass


class MsgSavedListHeader(MsgKey):
    pass


class MsgSavedListEmpty(MsgKey):
    pass


class MsgSavedListEntry(MsgKey):
    pass


# ── Catalogs ─────────────────────────────────────────────────────────


CATALOGS: dict[str, dict[type, str]] = {
    "en": {
        # Error strings (keyed by routing/local.py exceptions)
        TextTooLongError: ("Message is too long. Please keep it under 500 characters."),
        MessageHasNoTextError: "No message to process. Send a message first.",
        TextHasNoWrittenContentError: ("Please send text with actual written content."),
        UnauthorizedError: "Sorry, you are not authorized to use this bot.",
        # UI strings (MsgKey-keyed)
        MsgChooseAction: "What can I help you with?",
        MsgClear: "Okay thanks bye! Send another message if you need anything else ✨",
        MsgThinking: "🤔 Thinking...",
        MsgNoContent: "(no content)",
        MsgExpired: "This message has expired. Please send a new one.",
        MsgUnknownAction: "Unknown action.",
        MsgNoMessage: "No message to process. Send a message first.",
        MsgUnauthorized: "Sorry, you are not authorized to use this bot.",
        MsgAiError: "Error calling AI: {error}",
        MsgTooLong: "Message is too long. Please keep it under 500 characters.",
        # TODO: change to a template and populate with user's chosen languages
        MsgUnknownLanguage: (
            "Sorry, I couldn't detect the language."
            " Please send text in French or English."
        ),
        MsgWantToGoDeeper: "Want to go deeper? 🤿",
        MsgNoReplyText: (
            "Sorry, the original message could not be accessed. "
            "Please resend the message in this chat."
        ),
        MsgNoCorrectionsNeeded: "No corrections needed.",
        MsgChooseLanguage: "Which language would you like to learn?",
        MsgLanguageSelected: "You're learning {language}. Send me a message to get started.",
        MsgRateThisResponse: "Rate this response:",
        MsgSave: "💾 Save",
        MsgSaved: "✅ Saved",
        MsgSaveFailed: "Couldn't save that one. Please try again.",
        MsgSavedListHeader: "What you've kept:",
        MsgSavedListEmpty: (
            "Nothing kept yet. Tap 💾 Save on a reply to keep it for later."
        ),
        MsgSavedListEntry: "{index}. {anchor} — {action}, {date}",
    },
    # "fr": {
    #     TextTooLongError: "Le message est trop long. ...",
    #     ...
    # },
}


def t(key: type, locale: str = DEFAULT_LOCALE, **kwargs) -> str:
    """Resolve a UI string by key and locale, with English fallback."""
    catalog = CATALOGS.get(locale, CATALOGS[DEFAULT_LOCALE])
    template = catalog.get(key, CATALOGS[DEFAULT_LOCALE][key])
    return template.format(**kwargs) if kwargs else template
