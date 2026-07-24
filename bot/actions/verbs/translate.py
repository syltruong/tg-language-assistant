from typing import Any

from bot.actions.verbs.base import Action, LanguagePair


class TranslateAction(Action):
    def parse(self, raw: str) -> Any:
        return raw

    def format(self, validated_result: Any, language_pair: LanguagePair) -> str:
        return validated_result
