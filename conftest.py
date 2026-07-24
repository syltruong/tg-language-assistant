"""Root conftest: set dummy env vars so tests can import bot.config without real credentials."""

import os

os.environ.setdefault("TELEGRAM_TOKEN", "test-token")
os.environ.setdefault("OPENAI_API_KEY", "test-key")

# Force tracing off regardless of the developer's .env/shell — LangGraphLLMClient
# is exercised with a FakeLLMClient in tests, but the graph invocation still goes
# through LangChain's global tracer, which would otherwise send real traces to
# whatever LangSmith project the developer has configured for manual testing.
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
