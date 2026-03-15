from dataclasses import dataclass
from enum import StrEnum


class ActionType(StrEnum):
    """Bot actions available to users via inline keyboard buttons.

    Inherits from ``StrEnum`` so that each member *is* a ``str``.  This lets
    the values serve directly as Telegram ``callback_data``, ``PROMPTS`` dict
    keys, and comparison targets without ``.value`` boiler-plate.
    """

    TRANSLATE = "translate"
    TRANSLATE_WITH_CONTEXT = "translate_with_context"
    ANALYZE = "analyze"
    REPLY = "reply"
    CORRECT = "correct"
    REPHRASE = "rephrase"


@dataclass(frozen=True, slots=True)
class ReplySuggestion:
    reply: str
    tone: str
