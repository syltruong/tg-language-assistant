"""Pure helpers for building LangSmith trace metadata."""

import hashlib
from typing import Any


def hash_user_id(user_id: int) -> str:
    return hashlib.sha256(str(user_id).encode()).hexdigest()[:16]


def build_trace_metadata(
    *,
    action_type: str,
    base_language: str,
    target_language: str,
    detected_language: str,
    user_id: int,
    hash_user_id_enabled: bool,
) -> dict[str, Any]:
    return {
        "action_type": action_type,
        "base_language": base_language,
        "target_language": target_language,
        "detected_language": detected_language,
        "telegram_user_id": hash_user_id(user_id) if hash_user_id_enabled else user_id,
    }
