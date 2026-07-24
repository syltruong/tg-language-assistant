import os

from bot.actions.verbs.analyze import AnalyzeAction
from bot.actions.verbs.base import Action
from bot.actions.verbs.correct import CorrectAction
from bot.actions.verbs.rephrase import RephraseAction
from bot.actions.verbs.reply import ReplyAction
from bot.actions.verbs.translate import TranslateAction
from bot.localizer import Localizer
from bot.types import ActionType

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


def _load(name: str) -> str:
    with open(os.path.join(_PROMPTS_DIR, f"{name}.md"), encoding="utf-8") as f:
        return f.read().strip() + "\n\n"


class ActionRegistry:
    def __init__(self, localizer: Localizer) -> None:
        self._actions: dict[str, Action] = {
            ActionType.TRANSLATE: TranslateAction(
                localizer=localizer,
                prompt_template=_load("translate"),
                action_type=ActionType.TRANSLATE,
            ),
            ActionType.ANALYZE: AnalyzeAction(
                localizer=localizer,
                prompt_template=_load("analyze"),
                action_type=ActionType.ANALYZE,
            ),
            ActionType.CORRECT: CorrectAction(
                localizer=localizer,
                prompt_template=_load("correct"),
                action_type=ActionType.CORRECT,
            ),
            ActionType.REPHRASE: RephraseAction(
                localizer=localizer,
                prompt_template=_load("rephrase"),
                action_type=ActionType.REPHRASE,
            ),
            ActionType.REPLY: ReplyAction(
                localizer=localizer,
                prompt_template=_load("reply"),
                action_type=ActionType.REPLY,
            ),
        }

    def get(self, action_type: str) -> Action:
        return self._actions[action_type]
