from bot.tracing import build_trace_metadata, hash_user_id


class TestHashUserId:
    def test_is_deterministic_for_the_same_id(self):
        assert hash_user_id(12345) == hash_user_id(12345)

    def test_differs_across_ids(self):
        assert hash_user_id(1) != hash_user_id(2)

    def test_does_not_reveal_the_raw_id(self):
        assert "12345" not in hash_user_id(12345)


class TestBuildTraceMetadata:
    def test_includes_action_and_language_fields(self):
        metadata = build_trace_metadata(
            action_type="translate",
            base_language="en",
            target_language="fr",
            detected_language="en",
            user_id=42,
            hash_user_id_enabled=True,
        )

        assert metadata["action_type"] == "translate"
        assert metadata["base_language"] == "en"
        assert metadata["target_language"] == "fr"
        assert metadata["detected_language"] == "en"

    def test_hashes_user_id_when_enabled(self):
        metadata = build_trace_metadata(
            action_type="translate",
            base_language="en",
            target_language="fr",
            detected_language="en",
            user_id=42,
            hash_user_id_enabled=True,
        )

        assert metadata["telegram_user_id"] == hash_user_id(42)

    def test_keeps_raw_user_id_when_disabled(self):
        metadata = build_trace_metadata(
            action_type="translate",
            base_language="en",
            target_language="fr",
            detected_language="en",
            user_id=42,
            hash_user_id_enabled=False,
        )

        assert metadata["telegram_user_id"] == 42
