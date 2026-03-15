import os

from bot.types import ActionType

_PROMPTS_DIR = os.path.dirname(__file__)


def _load_system_prompt() -> str:
    path = os.path.join(_PROMPTS_DIR, "system.md")
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def _load_action_prompts() -> dict[ActionType, str]:
    prompts: dict[ActionType, str] = {}
    for action in ActionType:
        path = os.path.join(_PROMPTS_DIR, "actions", f"{action}.md")
        with open(path, encoding="utf-8") as f:
            prompts[action] = f.read().strip() + "\n\n"
    return prompts


SYSTEM_PROMPT = _load_system_prompt()
PROMPTS = _load_action_prompts()
