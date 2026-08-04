CREATE TABLE saved_insights (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           INTEGER NOT NULL,
    chat_id           INTEGER NOT NULL,
    slot_message_id   INTEGER NOT NULL,
    anchor_text       TEXT    NOT NULL,
    detected_language TEXT    NOT NULL,
    base_language     TEXT    NOT NULL,
    target_language   TEXT    NOT NULL,
    action_type       TEXT    NOT NULL,
    result_text       TEXT    NOT NULL,
    parse_mode        TEXT,
    run_id            TEXT,
    created_at        TEXT    NOT NULL,
    deleted_at        TEXT,

    -- One Saved Insight per turn per Action: re-tapping Save on the same view
    -- is a no-op, while Analyze-then-Correct on one turn yields two rows.
    UNIQUE (user_id, chat_id, slot_message_id, action_type)
);

CREATE INDEX idx_saved_insights_user_created
    ON saved_insights (user_id, created_at DESC);
