import logging
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

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
