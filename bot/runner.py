"""ActionRunner — executes the domain round-trip for any Action."""

from bot.actions.verbs.base import Action, LanguagePair
from bot.config import HASH_TELEGRAM_USER_ID, N_SUGGESTED_REPLIES
from bot.config.lang import LANGUAGE_NAMES
from bot.gateway import AnchorMessage, LanguageRole
from bot.llm_interface import LLMClient
from bot.tracing import build_trace_metadata
from bot.types import FormattedResult, Suggestion

_MAX_PARSE_RETRIES = 3


class FakeActionRunner:
    def __init__(
        self,
        result: str = "fake result",
        suggestions: "list[Suggestion] | None" = None,
        run_id: str | None = None,
    ) -> None:
        self._result = result
        self._suggestions = suggestions
        self._run_id = run_id
        self.last_action: Action | None = None
        self.last_anchor: AnchorMessage | None = None
        self.last_user_id: int = 0

    async def run(
        self,
        action: Action,
        anchor: AnchorMessage,
        language_pair: LanguagePair,
        user_id: int = 0,
    ) -> FormattedResult:
        self.last_action = action
        self.last_anchor = anchor
        self.last_user_id = user_id
        return FormattedResult(
            text=self._result,
            parse_mode=None,
            suggestions=self._suggestions,
            run_id=self._run_id,
        )


class ActionRunner:
    def __init__(self, llm: LLMClient, system_prompt_template: str) -> None:
        self._llm = llm
        self._system_prompt_template = system_prompt_template

    async def run(
        self,
        action: Action,
        anchor: AnchorMessage,
        language_pair: LanguagePair,
        user_id: int = 0,
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

        metadata = build_trace_metadata(
            action_type=action.action_type,
            base_language=language_pair.base,
            target_language=language_pair.target,
            detected_language=anchor.detected_language,
            user_id=user_id,
            hash_user_id_enabled=HASH_TELEGRAM_USER_ID,
        )

        for attempt in range(_MAX_PARSE_RETRIES):
            completion = await self._llm.complete(system_prompt, user_prompt, metadata=metadata)
            try:
                validated = action.parse(completion.text)
                text = action.format(validated, language_pair)
                suggestions = (
                    validated
                    if isinstance(validated, list)
                    and all(isinstance(s, Suggestion) for s in validated)
                    else None
                )
                return FormattedResult(
                    text=text,
                    parse_mode=action.parse_mode,
                    suggestions=suggestions,
                    run_id=completion.run_id,
                )
            except ValueError:
                if attempt == _MAX_PARSE_RETRIES - 1:
                    raise
