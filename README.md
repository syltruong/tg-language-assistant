Telegram Bot Boilerplate (python-telegram-bot)

Minimal starter for a Telegram bot using python-telegram-bot.

Quickstart (macOS / bash/zsh):

1. Create and activate a virtualenv:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variable:

```bash
cp .env.example .env
# edit .env and set TELEGRAM_TOKEN
```

4. Run the bot:

```bash
python -m bot.main
```

Files added:
- `requirements.txt` - pip dependencies
- `bot/main.py` - minimal bot app
- `.env.example` - sample token placeholder
- `.gitignore` - ignores venv and .env

Notes
- The bot reads `TELEGRAM_TOKEN` from the environment (via `python-dotenv`).
- This is a minimal starting point — add handlers and tests as needed.
