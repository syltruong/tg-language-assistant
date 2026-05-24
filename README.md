# Telegram Language Assistant

A Telegram bot that helps language learners communicate with native speakers in real time. Powered by OpenAI, it provides translation, vocabulary breakdowns, grammar analysis, and suggested replies.

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) for Python and dependency management

## Quickstart

```bash
cp .env.example .env   # set TELEGRAM_TOKEN and OPENAI_API_KEY
uv sync                # installs Python 3.12 (if needed) and all dependencies
```

## Running locally

**Polling (default)** — simplest, no extra setup:

```bash
make start
```

Requires [ngrok](https://ngrok.com/download) to be installed.

**Webhook via ngrok — one command:**

```bash
make start-webhook   # starts ngrok, wires up WEBHOOK_URL, starts the bot
```

**Webhook via ngrok — two terminals:**

```bash
# Terminal 1
ngrok http 8443

# Terminal 2 — paste the HTTPS URL printed by ngrok
WEBHOOK_URL=https://abc123.ngrok-free.app uv run python -m bot.main
```

> **Note:** only one instance of the bot should be running at a time. If the bot is deployed on fly.io with a webhook, starting it locally in polling mode will fail with a 409 from Telegram.

## Deploying

Pushes to `master` trigger an automatic deploy via GitHub Actions after lint and tests pass.

To deploy manually:

```bash
make fly-deploy
```

## Testing

Tests live next to the source files they cover (e.g. `bot/routing/test_local.py` tests `bot/routing/local.py`).

```bash
uv run pytest                # run all tests
uv run pytest -v             # verbose output with individual test names
uv run pytest bot/routing/   # run tests in a specific directory
uv run pytest -k "french"    # run only tests matching a keyword
```

## Linting

[Ruff](https://docs.astral.sh/ruff/) is used for linting and formatting. Run it with:

```bash
uv run ruff check .        # check for lint errors
uv run ruff check . --fix  # auto-fix fixable errors
uv run ruff format .       # format code
```

## Adding Python Dependencies

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. To add a new package:

```bash
uv add <package-name>          # add a runtime dependency
uv add --dev <package-name>    # add a development-only dependency
```

This updates `pyproject.toml` and `uv.lock` automatically. Commit both files so the change is reproducible for everyone.
