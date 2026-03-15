import os

from bot.types import InstantActionType, KeyboardActionType

_PROMPTS_DIR = os.path.dirname(__file__)


def _load_system_prompt() -> str:
    path = os.path.join(_PROMPTS_DIR, "system.md")
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def _load_instant_prompts() -> dict[InstantActionType, str]:
    prompts: dict[InstantActionType, str] = {}
    for action in InstantActionType:
        path = os.path.join(_PROMPTS_DIR, "actions", "instant", f"{action}.md")
        with open(path, encoding="utf-8") as f:
            prompts[action] = f.read().strip() + "\n\n"
    return prompts


def _load_keyboard_prompts() -> dict[KeyboardActionType, str]:
    prompts: dict[KeyboardActionType, str] = {}
    for action in KeyboardActionType:
        path = os.path.join(_PROMPTS_DIR, "actions", "keyboard", f"{action}.md")
        with open(path, encoding="utf-8") as f:
            prompts[action] = f.read().strip() + "\n\n"
    return prompts


SYSTEM_PROMPT = _load_system_prompt()
INSTANT_PROMPTS = _load_instant_prompts()
KEYBOARD_PROMPTS = _load_keyboard_prompts()
