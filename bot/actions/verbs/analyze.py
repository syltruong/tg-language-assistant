import json
from typing import Any

from bot.actions.verbs.base import Action, LanguagePair
from bot.localizer import Localizer

_REQUIRED_KEYS = {"vocabulary", "grammar"}


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _format_item(item: dict, primary_key: str | None = None) -> str:
    key_order = [primary_key] if primary_key else []
    for k in item:
        if k != primary_key and item.get(k) not in (None, "") and k not in key_order:
            key_order.append(k)
    lines = []
    for k in key_order:
        v = item.get(k)
        if v is None or v == "":
            continue
        v = str(v).strip()
        if k == primary_key:
            lines.append(f"• <b>{_escape(v)}</b>")
        else:
            label = k.replace("_", " ").title()
            lines.append(f"  <i>{label}</i>: {_escape(v)}")
    return "\n".join(lines)


class AnalyzeAction(Action):
    def __init__(self, localizer: Localizer, prompt_template: str) -> None:
        super().__init__(localizer, prompt_template)

    def parse(self, raw: str) -> Any:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e
        missing = _REQUIRED_KEYS - data.keys()
        if missing:
            raise ValueError(f"Missing required keys: {missing}")
        return data

    def format(self, validated_result: Any, language_pair: LanguagePair) -> str:
        data = validated_result
        parts = []
        known_lists = {"vocabulary": "form_in_text", "grammar": "quote"}
        for key, value in data.items():
            if key in known_lists and isinstance(value, list):
                primary = known_lists[key]
                title = key.replace("_", " ").title()
                lines = [
                    _format_item(item if isinstance(item, dict) else {}, primary)
                    for item in value
                ]
                block = "\n\n".join(line for line in lines if line.strip())
                if block:
                    parts.append(f"<b>{title}</b>\n{block}")
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                title = key.replace("_", " ").title()
                lines = [_format_item(i) for i in value]
                block = "\n\n".join(line for line in lines if line.strip())
                if block:
                    parts.append(f"<b>{title}</b>\n{block}")
            elif isinstance(value, (str, int, float, bool)) and value:
                title = key.replace("_", " ").title()
                parts.append(f"<b>{title}</b>\n{_escape(str(value))}")
            elif isinstance(value, dict) and value:
                title = key.replace("_", " ").title()
                parts.append(f"<b>{title}</b>\n{_format_item(value)}")
        return (
            "\n\n".join(parts)
            if parts
            else "No vocabulary or grammar points for this text."
        )
