import logging
import uuid
from dataclasses import dataclass
from typing import Any, Protocol, TypedDict, runtime_checkable

from langgraph.graph import StateGraph
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LLMCompletion:
    text: str
    run_id: str | None = None


@runtime_checkable
class LLMClient(Protocol):
    async def complete(
        self, system_prompt: str, user_prompt: str, *, metadata: dict[str, Any] | None = None
    ) -> LLMCompletion: ...


class FakeLLMClient:
    def __init__(self, response: str = "", run_id: str | None = None) -> None:
        self._response = response
        self._run_id = run_id
        self.last_metadata: dict[str, Any] | None = None

    async def complete(
        self, system_prompt: str, user_prompt: str, *, metadata: dict[str, Any] | None = None
    ) -> LLMCompletion:
        self.last_metadata = metadata
        return LLMCompletion(text=self._response, run_id=self._run_id)


class OpenAILLMClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def complete(
        self, system_prompt: str, user_prompt: str, *, metadata: dict[str, Any] | None = None
    ) -> LLMCompletion:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        logger.debug("messages: %s", messages)
        response = await self._client.responses.create(
            model=self._model,
            input=messages,
        )
        return LLMCompletion(text=response.output_text, run_id=None)


class _CompletionState(TypedDict):
    system_prompt: str
    user_prompt: str
    output: str


def _build_completion_graph(inner: LLMClient):
    async def call_llm(state: _CompletionState) -> _CompletionState:
        completion = await inner.complete(state["system_prompt"], state["user_prompt"])
        return {**state, "output": completion.text}

    graph = StateGraph(_CompletionState)
    graph.add_node("call_llm", call_llm)
    graph.set_entry_point("call_llm")
    graph.set_finish_point("call_llm")
    return graph.compile()


def _build_tags(metadata: dict[str, Any]) -> list[str]:
    tags = []
    if "action_type" in metadata:
        tags.append(f"action:{metadata['action_type']}")
    if "base_language" in metadata and "target_language" in metadata:
        tags.append(f"pair:{metadata['base_language']}-{metadata['target_language']}")
    return tags


class LangGraphLLMClient:
    """Traces LLM calls through a single-node, checkpointer-less LangGraph graph.

    No multi-turn state is kept — this is purely the tracing seam for
    LangSmith. Wraps any LLMClient so the underlying model call stays
    swappable and testable via FakeLLMClient.
    """

    def __init__(self, inner: LLMClient) -> None:
        self._inner = inner
        self._graph = _build_completion_graph(inner)

    async def complete(
        self, system_prompt: str, user_prompt: str, *, metadata: dict[str, Any] | None = None
    ) -> LLMCompletion:
        run_id = uuid.uuid4()
        result = await self._graph.ainvoke(
            {"system_prompt": system_prompt, "user_prompt": user_prompt, "output": ""},
            config={
                "run_id": run_id,
                "run_name": "llm_complete",
                "tags": _build_tags(metadata) if metadata else [],
                "metadata": metadata or {},
            },
        )
        return LLMCompletion(text=result["output"], run_id=str(run_id))
