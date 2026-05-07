import json
from typing import Any

from bot.actions.verbs.base import Action, LanguagePair
from bot.localizer import Localizer


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class RephraseAction(Action):
    def __init__(self, localizer: Localizer, prompt_template: str) -> None:
        super().__init__(localizer, prompt_template)

    @property
    def parse_mode(self) -> str | None:
        return "HTML"

    def parse(self, raw: str) -> Any:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e
        if not isinstance(data, list):
            raise ValueError(f"Expected a JSON array, got {type(data).__name__}")
        return data

    def format(self, validated_result: Any, language_pair: LanguagePair) -> str:
        parts = []
        for item in validated_result:
            if not isinstance(item, dict):
                continue
            rephrasing = _escape(str(item.get("rephrasing", "")).strip())
            note = _escape(str(item.get("note", "")).strip())
            if rephrasing:
                line = f"• {rephrasing}"
                if note:
                    line += f"  <i>({note})</i>"
                parts.append(line)
        return (
            "\n\n".join(parts)
            if parts
            else "Could not generate rephrasings. Please try again."
        )
