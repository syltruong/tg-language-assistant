import json

from bot.actions.verbs.base import Action, LanguagePair
from bot.localizer import Localizer
from bot.types import Suggestion


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class RephraseAction(Action):
    def __init__(self, localizer: Localizer, prompt_template: str) -> None:
        super().__init__(localizer, prompt_template)

    @property
    def parse_mode(self) -> str | None:
        return "HTML"

    def parse(self, raw: str) -> list[Suggestion]:
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
            text = str(item.get("text", "")).strip()
            note = str(item.get("note", "")).strip()
            if not text:
                raise ValueError("text field is blank")
            suggestions.append(Suggestion(text=text, note=note))
        return suggestions

    def format(self, validated_result: list[Suggestion], language_pair: LanguagePair) -> str:
        parts = []
        for s in validated_result:
            text = _escape(s.text)
            note = _escape(s.note)
            if text:
                line = f"• {text}"
                if note:
                    line += f"  <i>({note})</i>"
                parts.append(line)
        return "\n\n".join(parts)
