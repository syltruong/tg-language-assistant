"""Root conftest: set dummy env vars so tests can import bot.config without real credentials."""

import os

os.environ.setdefault("TELEGRAM_TOKEN", "test-token")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
