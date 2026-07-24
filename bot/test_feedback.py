from unittest.mock import MagicMock

from bot.feedback import FakeFeedbackClient, FeedbackClient, LangSmithFeedbackClient


class TestFakeFeedbackClient:
    async def test_records_run_id_is_good_and_comment(self):
        client = FakeFeedbackClient()

        await client.record_feedback("run-abc", True, comment="great")

        assert client.recorded == [("run-abc", True, "great")]

    async def test_comment_defaults_to_none(self):
        client = FakeFeedbackClient()

        await client.record_feedback("run-abc", False)

        assert client.recorded == [("run-abc", False, None)]

    async def test_satisfies_feedback_client_protocol(self):
        client = FakeFeedbackClient()
        assert isinstance(client, FeedbackClient)


class TestLangSmithFeedbackClient:
    async def test_calls_create_feedback_with_run_id_is_good_key_and_score(self):
        stub = MagicMock()
        client = LangSmithFeedbackClient(client=stub)

        await client.record_feedback("run-abc", True, comment="nice")

        stub.create_feedback.assert_called_once_with(
            run_id="run-abc", key="is_good", score=True, comment="nice"
        )

    async def test_swallows_errors_from_an_unreachable_backend(self):
        stub = MagicMock()
        stub.create_feedback.side_effect = ConnectionError("unreachable")
        client = LangSmithFeedbackClient(client=stub)

        await client.record_feedback("run-abc", True)  # must not raise

    async def test_satisfies_feedback_client_protocol(self):
        client = LangSmithFeedbackClient(client=MagicMock())
        assert isinstance(client, FeedbackClient)
