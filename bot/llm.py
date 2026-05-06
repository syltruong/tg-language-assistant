import asyncio
import time
from collections.abc import AsyncIterator
from typing import Protocol, TypeVar, runtime_checkable

import openai
from loguru import logger
from openai import AsyncOpenAI
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class LLMClient(Protocol):
    async def complete(self, system: str, user: str) -> str: ...
    async def complete_structured(
        self, system: str, user: str, response_model: type[T]
    ) -> T: ...
    async def stream(self, system: str, user: str) -> AsyncIterator[str]: ...


def _build_messages(system_prompt: str, user_prompt: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


class OpenAILLMClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        max_attempts: int = 3,
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._max_attempts = max_attempts

    async def complete(self, system: str, user: str) -> str:
        messages = _build_messages(system, user)
        for attempt in range(1, self._max_attempts + 1):
            try:
                t0 = time.perf_counter()
                response = await self._client.responses.create(
                    model=self._model,
                    input=messages,
                )
                elapsed = time.perf_counter() - t0
                usage = getattr(response, "usage", None)
                input_tokens = getattr(usage, "input_tokens", None) if usage else None
                output_tokens = getattr(usage, "output_tokens", None) if usage else None
                logger.debug(
                    "complete: latency={latency:.3f}s input_tokens={input_tokens} output_tokens={output_tokens}",
                    latency=elapsed,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
                return response.output_text
            except (openai.RateLimitError, openai.APITimeoutError) as exc:
                if attempt == self._max_attempts:
                    raise
                backoff = 2 ** (attempt - 1)
                logger.warning(
                    "LLM request failed (attempt {attempt}/{max}): {exc}; retrying in {backoff}s",
                    attempt=attempt,
                    max=self._max_attempts,
                    exc=exc,
                    backoff=backoff,
                )
                await asyncio.sleep(backoff)
        raise RuntimeError("unreachable")

    async def complete_structured(
        self, system: str, user: str, response_model: type[T]
    ) -> T:
        messages = _build_messages(system, user)
        schema = response_model.model_json_schema()
        name = schema.get("title", response_model.__name__)
        for attempt in range(1, self._max_attempts + 1):
            try:
                t0 = time.perf_counter()
                response = await self._client.responses.create(
                    model=self._model,
                    input=messages,
                    text={
                        "format": {
                            "type": "json_schema",
                            "name": name,
                            "schema": schema,
                            "strict": True,
                        }
                    },
                )
                elapsed = time.perf_counter() - t0
                usage = getattr(response, "usage", None)
                input_tokens = getattr(usage, "input_tokens", None) if usage else None
                output_tokens = getattr(usage, "output_tokens", None) if usage else None
                logger.debug(
                    "complete_structured: latency={latency:.3f}s input_tokens={input_tokens} output_tokens={output_tokens}",
                    latency=elapsed,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
                return response_model.model_validate_json(response.output_text)
            except (openai.RateLimitError, openai.APITimeoutError) as exc:
                if attempt == self._max_attempts:
                    raise
                backoff = 2 ** (attempt - 1)
                logger.warning(
                    "LLM structured request failed (attempt {attempt}/{max}): {exc}; retrying in {backoff}s",
                    attempt=attempt,
                    max=self._max_attempts,
                    exc=exc,
                    backoff=backoff,
                )
                await asyncio.sleep(backoff)
        raise RuntimeError("unreachable")

    async def stream(self, system: str, user: str) -> AsyncIterator[str]:
        messages = _build_messages(system, user)
        t0 = time.perf_counter()
        api_stream = await self._client.responses.create(
            model=self._model,
            input=messages,
            stream=True,
        )

        async def _iter() -> AsyncIterator[str]:
            async for event in api_stream:
                if event.type == "response.output_text.delta":
                    yield event.delta
            elapsed = time.perf_counter() - t0
            logger.debug("stream: latency={latency:.3f}s", latency=elapsed)

        return _iter()


class FakeLLMClient:
    """In-process test double — no network, no mock.patch."""

    def __init__(
        self,
        complete_return: str = "",
        stream_chunks: list[str] | None = None,
        structured_return: BaseModel | None = None,
    ) -> None:
        self.complete_return = complete_return
        self.stream_chunks = stream_chunks if stream_chunks is not None else []
        self.structured_return = structured_return
        self.complete_calls: list[tuple[str, str]] = []
        self.stream_calls: list[tuple[str, str]] = []
        self.structured_calls: list[tuple[str, str]] = []

    async def complete(self, system: str, user: str) -> str:
        self.complete_calls.append((system, user))
        return self.complete_return

    async def complete_structured(
        self, system: str, user: str, response_model: type[T]
    ) -> T:
        self.structured_calls.append((system, user))
        if self.structured_return is None:
            raise ValueError("FakeLLMClient.structured_return not set")
        return self.structured_return  # type: ignore[return-value]

    async def stream(self, system: str, user: str) -> AsyncIterator[str]:
        self.stream_calls.append((system, user))
        chunks = self.stream_chunks

        async def _iter() -> AsyncIterator[str]:
            for chunk in chunks:
                yield chunk

        return _iter()
