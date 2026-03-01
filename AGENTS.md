# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is a single-service **Telegram Language Assistant Bot** (Python 3.12, managed with `uv`). It uses the OpenAI API and the Telegram Bot API. There is no database, no monorepo structure, and no frontend.

### Running the bot

See `README.md` for quickstart. The command is `uv run python -m bot.main` (or `make start`).

### Required secrets

The bot **requires** two environment variables to start (even to import modules):
- `TELEGRAM_TOKEN` — Telegram bot token from BotFather
- `OPENAI_API_KEY` — OpenAI API key

Without these, `bot.config` raises `RuntimeError` at import time, so no modules from `bot` can be loaded.

### Linting and testing

There are **no linting tools or automated tests** configured in this project. No ruff, flake8, mypy, pytest, or similar. No `pre-commit` hooks either.

### Dependency management

- Package manager: `uv` (lockfile: `uv.lock`)
- Update script: `uv sync`
- Virtual environment is created at `.venv/` by `uv sync`
