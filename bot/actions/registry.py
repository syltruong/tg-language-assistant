import os

from bot.actions.verbs.base import Action
from bot.actions.verbs.analyze import AnalyzeAction
from bot.actions.verbs.correct import CorrectAction
from bot.actions.verbs.reply import ReplyAction
from bot.actions.verbs.rephrase import RephraseAction
from bot.actions.verbs.translate import TranslateAction
from bot.localizer import Localizer
from bot.types import ActionType

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts_v2")


def _load(path: str) -> str:
    with open(os.path.join(_PROMPTS_DIR, path), encoding="utf-8") as f:
        return f.read().strip() + "\n\n"


class ActionRegistry:
    def __init__(self, localizer: Localizer) -> None:
        self._actions: dict[str, Action] = {
            ActionType.TRANSLATE: TranslateAction(
                localizer=localizer,
                prompt_template=_load("actions/instant/translate.md"),
            ),
            ActionType.ANALYZE: AnalyzeAction(
                localizer=localizer,
                prompt_template=_load("actions/keyboard/analyze.md"),
            ),
            ActionType.CORRECT: CorrectAction(
                localizer=localizer,
                prompt_template=_load("actions/keyboard/correct.md"),
            ),
            ActionType.REPHRASE: RephraseAction(
                localizer=localizer,
                prompt_template=_load("actions/keyboard/rephrase.md"),
            ),
            ActionType.REPLY: ReplyAction(
                localizer=localizer,
                prompt_template=_load("actions/keyboard/reply.md"),
            ),
        }

    def get(self, action_type: str) -> Action:
        return self._actions[action_type]
