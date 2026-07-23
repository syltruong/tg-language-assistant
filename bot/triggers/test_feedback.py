import pytest

from bot.feedback import FakeFeedbackClient
from bot.keyboard import RATE_DOWN, RATE_UP
from bot.triggers.feedback import FeedbackTrigger
from tests.factories import make_callback_update, make_context


class TestFeedbackTrigger:
    @pytest.mark.asyncio
    async def test_thumbs_up_records_positive_score(self):
        feedback_client = FakeFeedbackClient()
        trigger = FeedbackTrigger(feedback_client=feedback_client)
        update = make_callback_update(callback_data=RATE_UP, message_id=77)
        context = make_context(user_data={"run_ids": {77: "run-abc"}})

        await trigger.handle(update, context)

        assert feedback_client.recorded == [("run-abc", 1.0, None)]

    @pytest.mark.asyncio
    async def test_thumbs_down_records_negative_score(self):
        feedback_client = FakeFeedbackClient()
        trigger = FeedbackTrigger(feedback_client=feedback_client)
        update = make_callback_update(callback_data=RATE_DOWN, message_id=77)
        context = make_context(user_data={"run_ids": {77: "run-abc"}})

        await trigger.handle(update, context)

        assert feedback_client.recorded == [("run-abc", 0.0, None)]

    @pytest.mark.asyncio
    async def test_missing_run_id_does_not_call_feedback_client(self):
        feedback_client = FakeFeedbackClient()
        trigger = FeedbackTrigger(feedback_client=feedback_client)
        update = make_callback_update(callback_data=RATE_UP, message_id=77)
        context = make_context()  # no run_ids stored

        await trigger.handle(update, context)

        assert feedback_client.recorded == []

    @pytest.mark.asyncio
    async def test_always_answers_the_callback_query(self):
        feedback_client = FakeFeedbackClient()
        trigger = FeedbackTrigger(feedback_client=feedback_client)
        update = make_callback_update(callback_data=RATE_UP, message_id=77)
        context = make_context()

        await trigger.handle(update, context)

        update.callback_query.answer.assert_called_once()
