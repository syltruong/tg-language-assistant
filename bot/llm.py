import logging
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from bot.config import MODEL_NAME, OPENAI_API_KEY

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    return _client


def _build_messages(system_prompt: str, user_prompt: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


async def get_completion(system_prompt: str, user_prompt: str) -> str:
    """Send a single (non-streaming) request and return the full response text."""
    model_input = _build_messages(system_prompt, user_prompt)
    logger.debug("model_input: %s", model_input)

    response = await _get_client().responses.create(
        model=MODEL_NAME,
        input=model_input,
    )
    return response.output_text


async def stream_completion(system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
    """Yield text chunks from a streaming OpenAI response."""
    model_input = _build_messages(system_prompt, user_prompt)
    logger.debug("model_input: %s", model_input)
    stream = await _get_client().responses.create(
        model=MODEL_NAME,
        input=model_input,
        stream=True,
    )
    async for event in stream:
        if event.type == "response.output_text.delta":
            yield event.delta
