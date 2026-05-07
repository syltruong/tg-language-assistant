"""ActionRunner — executes the domain round-trip for any Action."""

from bot.actions.verbs.base import Action, LanguagePair
from bot.config import N_SUGGESTED_REPLIES
from bot.config.lang import LANGUAGE_NAMES
from bot.gateway import AnchorMessage, LanguageRole
from bot.llm_interface import LLMClient
from bot.types import FormattedResult

_MAX_PARSE_RETRIES = 3


class FakeActionRunner:
    def __init__(self, result: str = "fake result") -> None:
        self._result = result
        self.last_action: Action | None = None
        self.last_anchor: AnchorMessage | None = None

    async def run(
        self,
        action: Action,
        anchor: AnchorMessage,
        language_pair: LanguagePair,
    ) -> FormattedResult:
        self.last_action = action
        self.last_anchor = anchor
        return FormattedResult(text=self._result, parse_mode=None)


class ActionRunner:
    def __init__(self, llm: LLMClient, system_prompt_template: str) -> None:
        self._llm = llm
        self._system_prompt_template = system_prompt_template

    async def run(
        self,
        action: Action,
        anchor: AnchorMessage,
        language_pair: LanguagePair,
    ) -> FormattedResult:
        base_name = LANGUAGE_NAMES[language_pair.base]
        target_name = LANGUAGE_NAMES[language_pair.target]
        from_name = LANGUAGE_NAMES[anchor.detected_language]
        to_name = (
            base_name if anchor.language_role == LanguageRole.TARGET else target_name
        )

        system_prompt = self._system_prompt_template.format(
            base_language=base_name,
            target_language=target_name,
        )
        user_prompt = action.prompt_template.format(
            text=anchor.text,
            base_language=base_name,
            target_language=target_name,
            from_language=from_name,
            to_language=to_name,
            n=N_SUGGESTED_REPLIES,
        )

        for attempt in range(_MAX_PARSE_RETRIES):
            raw = await self._llm.complete(system_prompt, user_prompt)
            try:
                text = action.format(action.parse(raw), language_pair)
                return FormattedResult(text=text, parse_mode=action.parse_mode)
            except ValueError:
                if attempt == _MAX_PARSE_RETRIES - 1:
                    raise
