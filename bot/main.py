from dotenv import load_dotenv
import logging
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from openai import AsyncOpenAI

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is not set. See .env.example")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set. See .env.example")

# Feature flags / tuning
# Set ENABLE_STREAMING=0 to disable streaming and always use the non-streaming path.
STREAMING_ENABLED = os.getenv("ENABLE_STREAMING", "1").lower() in ("1", "true", "yes", "on")
# Number of characters to accumulate before sending an edit update to Telegram
STREAM_CHUNK_SIZE = int(os.getenv("STREAM_CHUNK_SIZE", "40"))
# Model selection via environment variable
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


# Load system context and prompt templates from markdown files

def _load_system_prompt():
    path = os.path.join(os.path.dirname(__file__), "system_prompt.md")
    with open(path, encoding="utf-8") as f:
        return f.read().strip()

SYSTEM_PROMPT = _load_system_prompt()


def _load_button_prompts():
    """Parse button_prompts.md into a dict keyed by heading."""
    path = os.path.join(os.path.dirname(__file__), "button_prompts.md")
    prompts = {}
    current = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("## "):
                current = line[3:].strip()
                prompts[current] = ""
            elif current is not None:
                prompts[current] += line
    # ensure each value ends with two newlines for separation
    return {k: v.strip() + "\n\n" for k, v in prompts.items()}

PROMPTS = _load_button_prompts()



def _make_keyboard() -> InlineKeyboardMarkup:
    """Return the standard action keyboard with a cancel/clear button."""
    keyboard = [
        [
            InlineKeyboardButton(" Translate", callback_data="translate"),
            InlineKeyboardButton("🍎 Vocab", callback_data="vocab"),
        ],
        [
            InlineKeyboardButton("🧑‍💻 Syntax", callback_data="syntax"),
            InlineKeyboardButton("💬 Reply", callback_data="reply"),
        ],
        [
            # provide a button to clear the keyboard if user doesn't want to choose an action
            InlineKeyboardButton("Cancel", callback_data="clear"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Limit input to 100 characters
    if len(update.message.text) > 100:
        await update.message.reply_text(
            "Message is too long. Please keep it under 100 characters.",
            reply_to_message_id=update.message.message_id,
        )
        return

    reply_markup = _make_keyboard()
    # Store the message text in context for later use by callback handler
    context.user_data["last_message"] = update.message.text
    await update.message.reply_text(
        text="What can I help you with?",
        reply_markup=reply_markup,
        reply_to_message_id=update.message.message_id,
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks and call OpenAI with appropriate prompt."""
    query = update.callback_query
    await query.answer()  # Acknowledge the button press

    callback_data = query.data
    # special case for clearing the keyboard
    if callback_data == "clear":
        # simply remove the inline keyboard by editing the message
        await query.edit_message_text(text="Okay thanks bye! Send another message if you need anything else ✨")
        return

    if callback_data not in PROMPTS:
        await query.edit_message_text(text="Unknown action.")
        return

    # Get the original message from user_data
    original_text = context.user_data.get("last_message", "")
    if not original_text:
        await query.edit_message_text(text="No message to process. Send a message first.")
        return

    # Show "thinking" message
    await query.edit_message_text(text="🤔 Thinking...")

    try:
        # Build the prompt
        prompt = PROMPTS[callback_data] + original_text

        # If streaming is enabled, attempt to stream and progressively edit.
        if STREAMING_ENABLED:
            try:
                logging.info(
                    "Starting streaming for user=%s action=%s",
                    getattr(query.from_user, "id", None),
                    callback_data,
                )
                stream = await client.responses.create(
                    model=MODEL_NAME,
                    input=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    stream=True,
                )

                accumulated = ""
                last_sent_len = 0
                # start from an empty message so edits update the same message
                await query.edit_message_text(text="", reply_markup=None)

                async for event in stream:
                    # event structure may vary; attempt to extract token delta
                    chunk = ""
                    try:
                        chunk = event.choices[0].delta.content
                    except Exception:
                        try:
                            chunk = event.choices[0].delta.get("content", "")
                        except Exception:
                            chunk = ""
                    if not chunk:
                        continue
                    # log received chunk size (debug)
                    logging.debug("Received chunk size=%d for user=%s", len(chunk), getattr(query.from_user, "id", None))
                    accumulated += chunk
                    if len(accumulated) - last_sent_len >= STREAM_CHUNK_SIZE:
                        await query.edit_message_text(text=accumulated, reply_markup=_make_keyboard())
                        last_sent_len = len(accumulated)
                        logging.info(
                            "Sent edit update (%d chars) for user=%s",
                            last_sent_len,
                            getattr(query.from_user, "id", None),
                        )

                # final edit
                await query.edit_message_text(text=accumulated or "(no content)", reply_markup=_make_keyboard())
                logging.info(
                    "Streaming finished for user=%s total_chars=%d",
                    getattr(query.from_user, "id", None),
                    len(accumulated),
                )

            except Exception as e:
                logging.warning("Streaming failed, falling back to non-streaming: %s", e)
                # fallback to non-streaming below
                response = await client.responses.create(
                    model=MODEL_NAME,
                    input=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                )
                llm_reply = response.output_text
                await query.edit_message_text(text=llm_reply, reply_markup=_make_keyboard())

        else:
            # Streaming disabled — use a single request
            response = await client.responses.create(
                model=MODEL_NAME,
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
            llm_reply = response.output_text
            await query.edit_message_text(text=llm_reply, reply_markup=_make_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)

    except Exception as e:
        logging.error(f"OpenAI API error: {e}")
        await query.edit_message_text(text=f"Error calling AI: {str(e)}")


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.run_polling()


if __name__ == "__main__":
    main()
