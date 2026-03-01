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

### Full button user flow

Improve the conversational flow so users can chain actions and navigate between steps.

- [ ] Let users chain actions on the same text without losing context (e.g. translate, then vocab, then reply — in sequence)
- [ ] Add a "Back" button to return to the previous menu or result
- [ ] Replace the current "Cancel" behavior (which removes the keyboard entirely) with a "Close" button that can reopen the menu
- [ ] Add a `/help` command explaining available actions and the flow
- [ ] Track conversation state so the bot can offer contextual follow-ups (e.g. after translating, suggest "Want to check the vocab?")

### Correct mode

A new mode where the user practices writing in the target language and gets corrections.

- [ ] Add a "Correct" button to the inline keyboard
- [ ] User writes a sentence in the target language; the bot identifies grammar, spelling, and usage errors
- [ ] Return the corrected sentence with inline annotations explaining each fix
- [ ] Optionally rate the attempt (e.g. beginner/intermediate/advanced) and suggest what to study
- [ ] Wire up a dedicated LLM prompt for correction in `button_prompts.md`

### Database logging

Replace in-memory state with persistent storage for preferences, history, and analytics.

- [ ] Choose and integrate a lightweight database (e.g. SQLite via `aiosqlite`, or PostgreSQL for production)
- [ ] Persist user preferences (target language, settings) so they survive bot restarts
- [ ] Log all user messages and bot responses with timestamps for debugging and analytics
- [ ] Build a vocabulary/history feature so users can review their past lookups (e.g. `/history` command)
- [ ] Add retention policies or limits so the database doesn't grow unbounded
