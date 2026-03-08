# Telegram Language Assistant

A Telegram bot that helps language learners communicate with native speakers in real time. Powered by OpenAI, it provides translation, vocabulary breakdowns, grammar analysis, and suggested replies.

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) for Python and dependency management

## Quickstart

```bash
cp .env.example .env   # set TELEGRAM_TOKEN and OPENAI_API_KEY
uv sync                # installs Python 3.12 (if needed) and all dependencies
uv run python -m bot.main
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

## Roadmap

### Multi-lingual support

Currently the bot is hardcoded for French. Add the ability for users to choose their target language.

- [ ] Add a `/start` or `/settings` command that lets users pick their base langugage and a target language (e.g. French, Spanish, German, etc.)
- [ ] Store the user's language selection so it persists across sessions (see database task)
- [ ] Templatize the system prompt and button prompts so they dynamically adapt to the chosen language
- [ ] Update the translate button to use the selected language pair instead of hardcoded French/English

### Output validation

Cross-check LLM outputs for accuracy before delivering them to the user.

- [ ] After each action, score the output and re-run action N times until the output score goes over the threshold
- [ ] Add a validation loop for structured LLM outputs (e.g. JSON reply suggestions): retry the same prompt up to N times if parsing fails

### Full button user flow

Improve the conversational flow so users can chain actions and navigate between steps.

- [ ] Let users chain actions on the same text without losing context (e.g. translate, then vocab, then reply — in sequence)
- [ ] Add a "Back" button to return to the previous menu or result
- [ ] Replace the current "Cancel" behavior (which removes the keyboard entirely) with a "Close" button that can reopen the menu
- [ ] Add a `/help` command explaining available actions and the flow

### ✅ Correct mode

A new mode where the user practices writing in the target language and gets corrections.

- [x] Add a "Correct" button to the inline keyboard
- [x] User writes a sentence in the target language; the bot identifies grammar, spelling, and usage errors
- [x] Return the corrected sentence with inline annotations explaining each fix
- [x] Optionally rate the attempt (e.g. beginner/intermediate/advanced) and suggest what to study
- [x] Wire up a dedicated LLM prompt for correction in `button_prompts.md`

### Response caching

Cache LLM responses to avoid redundant API calls when the same (or similar) prompt is sent multiple times.

- [ ] Implement a cache layer keyed on (action, input text) pairs to return stored responses for repeated requests
- [ ] Choose a caching strategy (in-memory LRU, Redis, or database-backed) with configurable TTL and max size
- [ ] Add cache-hit/miss logging for observability

### Database logging

Replace in-memory state with persistent storage for preferences, history, and analytics.

- [ ] Choose and integrate a lightweight database (e.g. SQLite via `aiosqlite`, or PostgreSQL for production)
- [ ] Persist user preferences (target language, settings) so they survive bot restarts
- [ ] Log all user messages and bot responses with timestamps for debugging and analytics
- [ ] Build a vocabulary/history feature so users can review their past lookups (e.g. `/history` command)
- [ ] Add retention policies or limits so the database doesn't grow unbounded

### Safety guardrails

Protect users and the bot from harmful, off-topic, or adversarial content.

- [ ] Add input filtering to detect and reject prompt-injection attempts inside user messages
- [ ] Screen LLM outputs for toxic, harmful, or off-topic content before delivering them to the user
- [ ] Implement rate limiting per user to prevent abuse and runaway API costs
- [ ] Add a content moderation layer (e.g. OpenAI Moderation API) as a pre/post-processing step
