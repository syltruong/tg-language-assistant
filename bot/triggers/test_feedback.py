import pytest

from bot.feedback import FakeFeedbackClient
from bot.keyboard import RATE_DOWN, RATE_LABEL, RATE_UP, build_action_keyboard
from bot.triggers.feedback import FeedbackTrigger
from tests.factories import make_callback_update, make_context

KEYBOARD = build_action_keyboard()


class TestFeedbackTrigger:
    @pytest.mark.asyncio
    async def test_thumbs_up_records_is_good_true(self):
        feedback_client = FakeFeedbackClient()
        trigger = FeedbackTrigger(feedback_client=feedback_client)
        update = make_callback_update(callback_data=RATE_UP, message_id=77)
        update.callback_query.message.reply_markup = KEYBOARD
        context = make_context(user_data={"run_ids": {77: "run-abc"}})

        await trigger.handle(update, context)

        assert feedback_client.recorded == [("run-abc", True, None)]

    @pytest.mark.asyncio
    async def test_thumbs_down_records_is_good_false(self):
        feedback_client = FakeFeedbackClient()
        trigger = FeedbackTrigger(feedback_client=feedback_client)
        update = make_callback_update(callback_data=RATE_DOWN, message_id=77)
        update.callback_query.message.reply_markup = KEYBOARD
        context = make_context(user_data={"run_ids": {77: "run-abc"}})

        await trigger.handle(update, context)

        assert feedback_client.recorded == [("run-abc", False, None)]

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
        update.callback_query.message.reply_markup = KEYBOARD
        context = make_context(user_data={"run_ids": {77: "run-abc"}})

        await trigger.handle(update, context)

        update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_removes_the_rating_rows_after_recording_feedback(self):
        feedback_client = FakeFeedbackClient()
        trigger = FeedbackTrigger(feedback_client=feedback_client)
        update = make_callback_update(callback_data=RATE_UP, message_id=77)
        update.callback_query.message.reply_markup = KEYBOARD
        context = make_context(user_data={"run_ids": {77: "run-abc"}})

        await trigger.handle(update, context)

        update.callback_query.edit_message_reply_markup.assert_called_once()
        new_markup = update.callback_query.edit_message_reply_markup.call_args.kwargs["reply_markup"]
        assert new_markup.inline_keyboard == KEYBOARD.inline_keyboard[:-2]

    @pytest.mark.asyncio
    async def test_does_not_edit_markup_when_run_id_is_missing(self):
        feedback_client = FakeFeedbackClient()
        trigger = FeedbackTrigger(feedback_client=feedback_client)
        update = make_callback_update(callback_data=RATE_UP, message_id=77)
        context = make_context()  # no run_ids stored

        await trigger.handle(update, context)

        update.callback_query.edit_message_reply_markup.assert_not_called()

    @pytest.mark.asyncio
    async def test_tapping_the_label_row_is_a_safe_noop(self):
        feedback_client = FakeFeedbackClient()
        trigger = FeedbackTrigger(feedback_client=feedback_client)
        update = make_callback_update(callback_data=RATE_LABEL, message_id=77)
        update.callback_query.message.reply_markup = KEYBOARD
        context = make_context(user_data={"run_ids": {77: "run-abc"}})

        await trigger.handle(update, context)

        assert feedback_client.recorded == []
        update.callback_query.edit_message_reply_markup.assert_not_called()
        update.callback_query.answer.assert_called_once()
