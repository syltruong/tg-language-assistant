import logging
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from bot.config import OPENAI_API_KEY, MODEL_NAME

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


def _build_messages(system_prompt: str, user_prompt: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


async def get_completion(system_prompt: str, user_prompt: str) -> str:
    """Send a single (non-streaming) request and return the full response text."""
    model_input = _build_messages(system_prompt, user_prompt)
    logger.debug("model_input: %s", model_input)

    response = await client.responses.create(
        model=MODEL_NAME,
        input=model_input,
    )
    return response.output_text


async def stream_completion(prompt: str, system_prompt: str) -> AsyncIterator[str]:
    """Yield text chunks from a streaming OpenAI response."""
    model_input = _build_messages(system_prompt, user_prompt)
    logger.debug("model_input: %s", model_input)
    stream = await client.responses.create(
        model=MODEL_NAME,
        input=model_input,
        stream=True,
    )
    async for event in stream:
        chunk = ""
        try:
            chunk = event.choices[0].delta.content
        except Exception:
            try:
                chunk = event.choices[0].delta.get("content", "")
            except Exception:
                chunk = ""
        if chunk:
            yield chunk
