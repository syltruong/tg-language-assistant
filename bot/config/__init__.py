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
STREAMING_ENABLED = os.getenv("ENABLE_STREAMING", "1").lower() in (
    "1",
    "true",
    "yes",
    "on",
)

STREAM_CHUNK_SIZE = int(os.getenv("STREAM_CHUNK_SIZE", "40"))

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

# Optional: route the Chinese target language to a Qwen model via Alibaba Cloud's
# DashScope OpenAI-compatible endpoint. Leave QWEN_API_KEY unset to use MODEL_NAME
# for Chinese as well.
QWEN_API_KEY = os.getenv("QWEN_API_KEY")
QWEN_MODEL_NAME = os.getenv("QWEN_MODEL_NAME", "qwen-plus")
QWEN_BASE_URL = os.getenv(
    "QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)

N_SUGGESTED_REPLIES = int(os.getenv("N_SUGGESTED_REPLIES", "4"))

# Comma-separated Telegram user IDs. Empty means all users are allowed.
# To find your user ID, message @userinfobot on Telegram: https://t.me/userinfobot
_raw_allowed = os.getenv("ALLOWED_USERS", "")
ALLOWED_USERS: set[int] = {
    int(uid.strip())  # uid = numeric Telegram user ID
    for uid in _raw_allowed.split(",")
    if uid.strip()
}
