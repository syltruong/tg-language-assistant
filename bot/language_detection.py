"""Language detection graph: a deterministic detector with an LLM fallback.

Two-node LangGraph graph. `detect_deterministic` runs first; if its result
matches neither the user's base nor target language, a conditional edge
routes to `call_llm` (shared with `llm_interface.py`'s completion graph) to
double-check with the LLM before giving up.
"""

from typing import TypedDict

from langgraph.graph import END, StateGraph

from bot.actions.verbs.base import LanguagePair
from bot.config.lang import LANGUAGE_NAMES
from bot.errors import UnsupportedLanguageError
from bot.gateway import LanguageDetector, LanguageRole
from bot.llm_interface import LLMClient, build_call_llm_node


class LanguageDetectionState(TypedDict):
    text: str
    base: str
    target: str
    detected_language: str
    role: str | None
    system_prompt: str
    user_prompt: str
    output: str


def _classify(iso_code: str, base: str, target: str) -> LanguageRole | None:
    if iso_code == target:
        return LanguageRole.TARGET
    if iso_code == base:
        return LanguageRole.BASE
    return None


def _build_fallback_prompt(text: str, base: str, target: str) -> tuple[str, str]:
    base_name = LANGUAGE_NAMES.get(base, base)
    target_name = LANGUAGE_NAMES.get(target, target)
    system_prompt = (
        f"Is the following text written in {base_name} or {target_name}?"
        f" Reply with only the ISO code '{base}' or '{target}', or the word"
        " 'none' if it is neither."
    )
    return system_prompt, text


def _build_graph(language_detector: LanguageDetector, llm_client: LLMClient):
    async def detect_deterministic(state: LanguageDetectionState) -> LanguageDetectionState:
        iso_code = language_detector.detect(state["text"])
        role = _classify(iso_code, state["base"], state["target"])
        if role is not None:
            return {**state, "detected_language": iso_code, "role": role.value}

        system_prompt, user_prompt = _build_fallback_prompt(
            state["text"], state["base"], state["target"]
        )
        return {
            **state,
            "detected_language": iso_code,
            "role": None,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        }

    def route_after_deterministic(state: LanguageDetectionState) -> str:
        return END if state["role"] is not None else "call_llm"

    graph = StateGraph(LanguageDetectionState)
    graph.add_node("detect_deterministic", detect_deterministic)
    graph.add_node("call_llm", build_call_llm_node(llm_client))
    graph.set_entry_point("detect_deterministic")
    graph.add_conditional_edges(
        "detect_deterministic", route_after_deterministic, {END: END, "call_llm": "call_llm"}
    )
    graph.set_finish_point("call_llm")
    return graph.compile()


class GraphLanguageClassifier:
    def __init__(self, language_detector: LanguageDetector, llm_client: LLMClient) -> None:
        self._graph = _build_graph(language_detector, llm_client)

    async def classify(self, text: str, language_pair: LanguagePair) -> tuple[str, LanguageRole]:
        result = await self._graph.ainvoke(
            {
                "text": text,
                "base": language_pair.base,
                "target": language_pair.target,
                "detected_language": "",
                "role": None,
                "system_prompt": "",
                "user_prompt": "",
                "output": "",
            }
        )

        if result["role"] is not None:
            return result["detected_language"], LanguageRole(result["role"])

        fallback_iso = result["output"].strip().lower()
        fallback_role = _classify(fallback_iso, language_pair.base, language_pair.target)
        if fallback_role is None:
            raise UnsupportedLanguageError(base=language_pair.base, target=language_pair.target)
        return fallback_iso, fallback_role


class FakeLanguageClassifier:
    def __init__(self, iso_code: str, role: LanguageRole) -> None:
        self._iso_code = iso_code
        self._role = role

    async def classify(self, text: str, language_pair: LanguagePair) -> tuple[str, LanguageRole]:
        return self._iso_code, self._role
