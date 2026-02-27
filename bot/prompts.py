import os

_BOT_DIR = os.path.dirname(__file__)


def _load_system_prompt() -> str:
    path = os.path.join(_BOT_DIR, "system_prompt.md")
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def _load_button_prompts() -> dict[str, str]:
    """Parse button_prompts.md into a dict keyed by heading."""
    path = os.path.join(_BOT_DIR, "button_prompts.md")
    prompts: dict[str, str] = {}
    current = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("## "):
                current = line[3:].strip()
                prompts[current] = ""
            elif current is not None:
                prompts[current] += line
    return {k: v.strip() + "\n\n" for k, v in prompts.items()}


SYSTEM_PROMPT = _load_system_prompt()
PROMPTS = _load_button_prompts()
