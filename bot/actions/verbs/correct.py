import json
from typing import Any

from bot.actions.verbs.base import Action, LanguagePair, _escape
from bot.config.messages import MsgNoCorrectionsNeeded
from bot.localizer import Localizer

_ANNOTATION_KEYS = {"original", "correction", "explanation"}


class CorrectAction(Action):
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
        if "corrected" not in data:
            raise ValueError("Missing required key: corrected")
        if "annotations" not in data:
            raise ValueError("Missing required key: annotations")
        for annotation in data["annotations"]:
            missing = _ANNOTATION_KEYS - annotation.keys()
            if missing:
                raise ValueError(f"Annotation missing keys: {missing}")
        return data

    def format(self, validated_result: Any, language_pair: LanguagePair) -> str:
        data = validated_result
        corrected = _escape(data["corrected"])
        annotations = data["annotations"]
        if not annotations:
            no_corrections = self._localizer.t(MsgNoCorrectionsNeeded, locale=language_pair.base)
            return f"<b>{no_corrections}</b>\n\n{corrected}"
        blocks = [
            f"<s>{_escape(a['original'])}</s> → <b>{_escape(a['correction'])}</b>\n<i>{_escape(a['explanation'])}</i>"
            for a in annotations
        ]
        return corrected + "\n\n" + "\n\n".join(blocks)
