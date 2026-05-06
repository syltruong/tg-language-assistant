from typing import Any

from bot.actions.verbs.base import Action, LanguagePair
from bot.localizer import Localizer


class TranslateAction(Action):
    def __init__(self, localizer: Localizer, prompt_template: str) -> None:
        super().__init__(localizer, prompt_template)

    def parse(self, raw: str) -> Any:
        return raw

    def format(self, validated_result: Any, language_pair: LanguagePair) -> str:
        return validated_result
