import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is not set. See .env.example")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set. See .env.example")

# Set ENABLE_STREAMING=0 to disable streaming and always use the non-streaming path.
STREAMING_ENABLED = os.getenv("ENABLE_STREAMING", "1").lower() in ("1", "true", "yes", "on")

STREAM_CHUNK_SIZE = int(os.getenv("STREAM_CHUNK_SIZE", "40"))

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

N_SUGGESTED_REPLIES = int(os.getenv("N_SUGGESTED_REPLIES", "4"))

# Comma-separated Telegram user IDs. Empty means all users are allowed.
# To find your user ID, message @userinfobot on Telegram: https://t.me/userinfobot
_raw_allowed = os.getenv("ALLOWED_USERS", "")
ALLOWED_USERS: set[int] = {
    int(uid.strip())  # uid = numeric Telegram user ID
    for uid in _raw_allowed.split(",")
    if uid.strip()
}
