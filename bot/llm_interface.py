import logging
from typing import Protocol, runtime_checkable

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


@runtime_checkable
class LLMClient(Protocol):
    async def complete(self, system_prompt: str, user_prompt: str) -> str: ...


class FakeLLMClient:
    def __init__(self, response: str = "") -> None:
        self._response = response

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        return self._response


class OpenAILLMClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        logger.debug("messages: %s", messages)
        response = await self._client.responses.create(
            model=self._model,
            input=messages,
        )
        return response.output_text
