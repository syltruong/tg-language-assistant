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

    def test_satisfies_llm_client_protocol_with_qwen_style_config(self):
        client = OpenAILLMClient(
            api_key="test-key",
            model="qwen-plus",
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            use_chat_completions_api=True,
        )
        assert isinstance(client, LLMClient)
