import json

from bot.actions.verbs.base import Action, LanguagePair
from bot.localizer import Localizer
from bot.types import ReplySuggestion


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class ReplyAction(Action):
    def __init__(self, localizer: Localizer, prompt_template: str) -> None:
        super().__init__(localizer, prompt_template)

    @property
    def parse_mode(self) -> str | None:
        return "HTML"

    def parse(self, raw: str) -> list[ReplySuggestion]:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e
        if not isinstance(data, list):
            raise ValueError(f"Expected a JSON array, got {type(data).__name__}")
        if not data:
            raise ValueError("Expected a non-empty JSON array")
        suggestions = []
        for item in data:
            if not isinstance(item, dict):
                raise ValueError(f"Expected each item to be a dict, got {type(item).__name__}")
            reply = str(item.get("reply", "")).strip()
            tone = str(item.get("tone", "")).strip()
            if not reply:
                raise ValueError("Reply field is blank")
            if not tone:
                raise ValueError("Tone field is blank")
            suggestions.append(ReplySuggestion(reply=reply, tone=tone))
        return suggestions

    def format(self, validated_result: list[ReplySuggestion], language_pair: LanguagePair) -> str:
        parts = []
        for s in validated_result:
            reply = _escape(s.reply)
            tone = _escape(s.tone)
            if reply:
                line = f"• {reply}"
                if tone:
                    line += f"  <i>({tone})</i>"
                parts.append(line)
        return (
            "\n\n".join(parts)
            if parts
            else "Could not generate replies. Please try again."
        )
