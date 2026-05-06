import pytest

from bot.llm_interface import FakeLLMClient, LLMClient, OpenAILLMClient


class TestFakeLLMClient:
    async def test_complete_returns_configured_response(self):
        client = FakeLLMClient(response="bonjour")
        result = await client.complete("sys", "user")
        assert result == "bonjour"

    async def test_complete_default_response_is_empty_string(self):
        client = FakeLLMClient()
        result = await client.complete("sys", "user")
        assert result == ""


class TestOpenAILLMClientProtocol:
    def test_satisfies_llm_client_protocol(self):
        client = OpenAILLMClient(api_key="test-key", model="gpt-4o-mini")
        assert isinstance(client, LLMClient)
