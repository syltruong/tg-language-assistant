# TODO

- [ ] `bot/handlers/button.py:95` — add type hint for `query` parameter in `_handle_non_reply_action`
- [ ] provision for i8n in the UI messages and have a catalog of messages indexed by language
- [ ] write unit test harness for the bot 


## About unit tests for Telegram
For testing with `python-telegram-bot`, the key challenge is that everything is async and deeply tied to Telegram's API. Here's a practical approach:

### Core strategy: mock the `Update` and `Context` objects

These are the two objects passed to every handler, so you need to fake them convincingly.

```python
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes

def make_update(text: str, user_id: int = 123, chat_id: int = 456) -> Update:
    """Factory for fake Update objects."""
    user = MagicMock(spec=User)
    user.id = user_id
    user.is_bot = False

    chat = MagicMock(spec=Chat)
    chat.id = chat_id

    message = MagicMock(spec=Message)
    message.text = text
    message.from_user = user
    message.chat = chat
    message.reply_text = AsyncMock()  # ← critical: this is what your handlers call

    update = MagicMock(spec=Update)
    update.message = message
    update.effective_user = user
    update.effective_chat = chat

    return update

def make_context() -> MagicMock:
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    return context
```

### Writing the tests

```python
import pytest

@pytest.mark.asyncio
async def test_translation_handler_replies():
    from bot.handlers import handle_message  # your handler

    update = make_update("Bonjour tout le monde")
    context = make_context()

    with patch("bot.handlers.call_claude", new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = {
            "translation": "Hello everyone",
            "register": "casual",
            "one_line_context": "Standard greeting",
            "vocabulary": []
        }
        await handle_message(update, context)

    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "Hello everyone" in call_args
```

### What's worth unit testing vs not

**Worth testing:**
- Your **routing logic** — does a gibberish message skip the API call? Does a short message skip the analysis?
- Your **response formatting** — given a Claude JSON response, does the rendered Telegram HTML look right?
- Your **register detection** path — does `register: "formal"` produce a different output than `register: "casual"`?
- **`langdetect` threshold** — does a low-confidence detection fall through correctly?

**Not worth unit testing (integration/manual instead):**
- The actual Telegram webhook delivery
- Stripe webhooks
- Anything touching Supabase

### Practical setup

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"  # so you don't need @pytest.mark.asyncio on every test
```

```
pip install pytest pytest-asyncio --break-system-packages
```

The biggest win early on is testing your **formatting functions** in isolation — those pure functions that take a Claude JSON response and return an HTML string are trivially testable and catch a surprising number of bugs.
