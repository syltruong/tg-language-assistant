"""SavedListTrigger — shows the user what they have kept.

Deliberately minimal. Search, filtering and any derived view (vocabulary,
spaced repetition) are read-side concerns that can be built later from the
same rows, per ADR-0006.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.config.messages import (
    MsgSavedListEmpty,
    MsgSavedListEntry,
    MsgSavedListHeader,
)
from bot.insights import InsightRepositoryProtocol, SavedInsight
from bot.localizer import Localizer
from bot.session import UserSession

_MAX_ANCHOR_CHARS = 60


class SavedListTrigger:
    def __init__(
        self,
        repository: InsightRepositoryProtocol,
        localizer: Localizer,
    ) -> None:
        self._repository = repository
        self._localizer = localizer

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        session = UserSession.from_context(context)
        locale = session.base_language

        kept = await self._repository.list_for_user(user_id=update.effective_user.id)
        if not kept:
            await update.message.reply_text(self._localizer.t(MsgSavedListEmpty, locale))
            return

        lines = [self._localizer.t(MsgSavedListHeader, locale)]
        lines += [
            self._localizer.t(
                MsgSavedListEntry,
                locale,
                index=index,
                anchor=_shorten(insight.anchor_text),
                action=insight.action_type,
                date=_date_of(insight),
            )
            for index, insight in enumerate(kept, start=1)
        ]

        # Plain text, no parse_mode: entries carry user-supplied anchor text and
        # LLM output, neither of which is safe to hand to Telegram as markup.
        await update.message.reply_text("\n".join(lines))


def _shorten(text: str) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= _MAX_ANCHOR_CHARS:
        return collapsed
    return collapsed[: _MAX_ANCHOR_CHARS - 1] + "…"


def _date_of(insight: SavedInsight) -> str:
    return (insight.created_at or "")[:10]
