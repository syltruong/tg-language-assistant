import json
from typing import Any

from bot.actions.verbs.base import Action, LanguagePair
from bot.localizer import Localizer


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class ReplyAction(Action):
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
            reply = _escape(str(item.get("reply", "")).strip())
            tone = _escape(str(item.get("tone", "")).strip())
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
