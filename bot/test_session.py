from bot.session import UserSession


class TestUserSessionRunId:
    def test_stores_and_retrieves_run_id_for_a_message(self):
        session = UserSession({})

        session.store_run_id(123, "run-abc")

        assert session.get_run_id(123) == "run-abc"

    def test_returns_none_when_no_run_id_stored_for_message(self):
        session = UserSession({})

        assert session.get_run_id(999) is None
