from bot.llm_interface import (
    FakeLLMClient,
    LangGraphLLMClient,
    LLMClient,
    OpenAILLMClient,
)


class TestFakeLLMClient:
    async def test_complete_returns_configured_response(self):
        client = FakeLLMClient(response="bonjour")
        result = await client.complete("sys", "user")
        assert result.text == "bonjour"

    async def test_complete_default_response_is_empty_string(self):
        client = FakeLLMClient()
        result = await client.complete("sys", "user")
        assert result.text == ""

    async def test_complete_carries_configured_run_id(self):
        client = FakeLLMClient(response="bonjour", run_id="run-123")
        result = await client.complete("sys", "user")
        assert result.run_id == "run-123"

    async def test_complete_forwards_metadata_for_inspection(self):
        client = FakeLLMClient(response="bonjour")
        await client.complete("sys", "user", metadata={"action_type": "translate"})
        assert client.last_metadata == {"action_type": "translate"}


class TestOpenAILLMClientProtocol:
    def test_satisfies_llm_client_protocol(self):
        client = OpenAILLMClient(api_key="test-key", model="gpt-4o-mini")
        assert isinstance(client, LLMClient)


class TestLangGraphLLMClient:
    async def test_passes_through_the_inner_clients_text(self):
        client = LangGraphLLMClient(inner=FakeLLMClient(response="bonjour"))
        result = await client.complete("sys", "user")
        assert result.text == "bonjour"

    async def test_satisfies_llm_client_protocol(self):
        client = LangGraphLLMClient(inner=FakeLLMClient())
        assert isinstance(client, LLMClient)

    async def test_generates_a_run_id_without_any_langsmith_credentials(self):
        client = LangGraphLLMClient(inner=FakeLLMClient(response="bonjour"))
        result = await client.complete("sys", "user")
        assert result.run_id is not None
