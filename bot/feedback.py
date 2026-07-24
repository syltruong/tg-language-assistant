"""FeedbackClient — records a user's rating against a LangSmith trace."""

import asyncio
import logging
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class FeedbackClient(Protocol):
    async def record_feedback(
        self, run_id: str, is_good: bool, comment: str | None = None
    ) -> None: ...


class FakeFeedbackClient:
    def __init__(self) -> None:
        self.recorded: list[tuple[str, bool, str | None]] = []

    async def record_feedback(
        self, run_id: str, is_good: bool, comment: str | None = None
    ) -> None:
        self.recorded.append((run_id, is_good, comment))


class LangSmithFeedbackClient:
    def __init__(self, client: Any | None = None) -> None:
        from langsmith import Client

        self._client = client or Client()

    async def record_feedback(
        self, run_id: str, is_good: bool, comment: str | None = None
    ) -> None:
        try:
            await asyncio.to_thread(
                self._client.create_feedback,
                run_id=run_id,
                key="is_good",
                score=is_good,
                comment=comment,
            )
        except Exception:
            logger.warning("Failed to record LangSmith feedback for run_id=%s", run_id)
