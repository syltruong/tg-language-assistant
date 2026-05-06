from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from bot.localizer import Localizer


@dataclass(frozen=True)
class LanguagePair:
    base: str    # ISO code, e.g. "en"
    target: str  # ISO code, e.g. "fr"


class Action(ABC):
    def __init__(self, localizer: Localizer, prompt_template: str) -> None:
        self._localizer = localizer
        self.prompt_template = prompt_template

    @abstractmethod
    def parse(self, raw: str) -> Any:
        """Parse and validate the raw LLM string. Raises ValueError if invalid."""
        ...

    @abstractmethod
    def format(self, validated_result: Any, language_pair: LanguagePair) -> str: ...
