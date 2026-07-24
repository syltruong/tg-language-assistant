"""FeedbackTrigger — records a user's 👍/👎 tap against the rated message's trace."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.feedback import FeedbackClient
from bot.keyboard import RATE_DOWN, RATE_UP, strip_rating_rows
from bot.session import UserSession

_IS_GOOD = {RATE_UP: True, RATE_DOWN: False}


class FeedbackTrigger:
    def __init__(self, feedback_client: FeedbackClient) -> None:
        self._feedback_client = feedback_client

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        session = UserSession.from_context(context)
        msg_id = query.message.message_id
        run_id = session.get_run_id(msg_id)

        if run_id is None:
            await query.answer("Feedback unavailable for this message.")
            return

        is_good = _IS_GOOD.get(query.data)
        if is_good is None:
            await query.answer()
            return

        await self._feedback_client.record_feedback(run_id, is_good)
        await query.edit_message_reply_markup(
            reply_markup=strip_rating_rows(query.message.reply_markup)
        )
        await query.answer("Thanks for your feedback!")
