"""SaveTrigger — keeps the turn the user is looking at as a Saved Insight."""

from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes

from bot.config.messages import MsgSaved, MsgSaveFailed, t
from bot.insights import InsightRepositoryProtocol, SavedInsight
from bot.keyboard import build_action_keyboard
from bot.session import UserSession

# What the user saw, when we can no longer tell which Action rendered it.
UNKNOWN_ACTION = "unknown"


class SaveTrigger:
    """Writes a verbatim snapshot of the current turn.

    Per ADR-0006 this never calls the LLM and never depends on Session:
    the anchor and the rendered result both come off the callback, so a
    Save still lands after a restart. Session only supplies correlation
    extras (run_id, which Action rendered the slot) and their absence is
    recorded, not treated as failure.
    """

    def __init__(self, repository: InsightRepositoryProtocol) -> None:
        self._repository = repository

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        session = UserSession.from_context(context)
        slot_id = query.message.message_id
        language_pair = session.language_pair

        anchor = getattr(query.message, "reply_to_message", None)
        insight = SavedInsight(
            user_id=update.effective_user.id,
            chat_id=query.message.chat.id,
            slot_message_id=slot_id,
            anchor_text=(getattr(anchor, "text", "") or "").strip(),
            detected_language=session.get_detected_language(slot_id) or language_pair.target,
            base_language=language_pair.base,
            target_language=language_pair.target,
            action_type=session.get_slot_action(slot_id) or UNKNOWN_ACTION,
            result_text=query.message.text_html or query.message.text or "",
            parse_mode="HTML" if query.message.text_html else None,
            run_id=session.get_run_id(slot_id),
        )

        try:
            await self._repository.save(insight)
        except Exception as exc:  # never break the Telegram flow
            logger.warning("Could not save insight: {}", exc)
            await query.answer(t(MsgSaveFailed, session.base_language))
            return

        await query.answer(t(MsgSaved, session.base_language))
        await query.edit_message_reply_markup(reply_markup=build_action_keyboard(saved=True))
