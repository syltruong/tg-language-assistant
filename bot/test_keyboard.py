from bot.config.messages import MsgRateThisResponse, MsgSave, MsgSaved, MsgSkipFeedback, t
from bot.keyboard import (
    RATE_DOWN,
    RATE_LABEL,
    RATE_SKIP,
    RATE_UP,
    SAVE,
    build_action_keyboard,
    build_suggestions_keyboard,
    strip_rating_rows,
)
from bot.types import Suggestion

_SUGGESTIONS = [
    Suggestion(text="Bien merci!", note="warm"),
    Suggestion(text="Oui, ça va!", note="playful"),
]

KEYBOARD = build_action_keyboard()


class TestSaveRow:
    def test_action_keyboard_has_a_save_row_above_the_rating_rows(self):
        save_row = KEYBOARD.inline_keyboard[-3]

        assert [btn.callback_data for btn in save_row] == [SAVE]

    def test_save_button_label_comes_from_the_message_catalog(self):
        assert KEYBOARD.inline_keyboard[-3][0].text == t(MsgSave)

    def test_a_kept_turn_shows_the_saved_label(self):
        kept = build_action_keyboard(saved=True)

        assert kept.inline_keyboard[-3][0].text == t(MsgSaved)

    def test_suggestions_keyboard_has_no_save_row(self):
        """Suggestions are reply options — Save belongs to the action keyboard."""
        kb = build_suggestions_keyboard(_SUGGESTIONS)

        callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert SAVE not in callbacks


class TestRatingRow:
    def test_standard_keyboard_has_a_thumbs_row_last(self):
        last_row = KEYBOARD.inline_keyboard[-1]
        assert [btn.callback_data for btn in last_row] == [RATE_UP, RATE_DOWN, RATE_SKIP]

    def test_standard_keyboard_has_a_label_row_above_the_thumbs(self):
        label_row = KEYBOARD.inline_keyboard[-2]
        assert [btn.callback_data for btn in label_row] == [RATE_LABEL]

    def test_suggestions_keyboard_has_a_thumbs_row_last(self):
        kb = build_suggestions_keyboard(_SUGGESTIONS)
        last_row = kb.inline_keyboard[-1]
        assert [btn.callback_data for btn in last_row] == [RATE_UP, RATE_DOWN, RATE_SKIP]

    def test_suggestions_keyboard_has_a_label_row_above_the_thumbs(self):
        kb = build_suggestions_keyboard(_SUGGESTIONS)
        label_row = kb.inline_keyboard[-2]
        assert [btn.callback_data for btn in label_row] == [RATE_LABEL]

    def test_label_row_text_comes_from_the_message_catalog(self):
        label_row = KEYBOARD.inline_keyboard[-2]
        assert label_row[0].text == t(MsgRateThisResponse)

    def test_skip_button_text_comes_from_the_message_catalog(self):
        thumbs_row = KEYBOARD.inline_keyboard[-1]
        assert thumbs_row[2].text == t(MsgSkipFeedback)


class TestStripRatingRows:
    def test_removes_the_last_two_rows(self):
        stripped = strip_rating_rows(KEYBOARD)
        assert stripped.inline_keyboard == KEYBOARD.inline_keyboard[:-2]

    def test_removes_the_rating_rows_from_a_suggestions_keyboard(self):
        kb = build_suggestions_keyboard(_SUGGESTIONS)
        stripped = strip_rating_rows(kb)
        assert stripped.inline_keyboard == kb.inline_keyboard[:-2]


class TestBuildSuggestionsKeyboard:
    def test_one_button_row_per_suggestion_plus_rating_rows(self):
        kb = build_suggestions_keyboard(_SUGGESTIONS)
        assert len(kb.inline_keyboard) == 4

    def test_button_label_includes_number_and_note(self):
        kb = build_suggestions_keyboard(_SUGGESTIONS)
        assert kb.inline_keyboard[0][0].text == "1 · warm"
        assert kb.inline_keyboard[1][0].text == "2 · playful"

    def test_callback_data_is_select_colon_index(self):
        kb = build_suggestions_keyboard(_SUGGESTIONS)
        assert kb.inline_keyboard[0][0].callback_data == "select:0"
        assert kb.inline_keyboard[1][0].callback_data == "select:1"
