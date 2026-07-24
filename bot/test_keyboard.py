from bot.keyboard import (
    KEYBOARD,
    RATE_DOWN,
    RATE_UP,
    build_suggestions_keyboard,
    strip_rating_row,
)
from bot.types import Suggestion

_SUGGESTIONS = [
    Suggestion(text="Bien merci!", note="warm"),
    Suggestion(text="Oui, ça va!", note="playful"),
]


class TestRatingRow:
    def test_standard_keyboard_has_a_rating_row(self):
        last_row = KEYBOARD.inline_keyboard[-1]
        assert [btn.callback_data for btn in last_row] == [RATE_UP, RATE_DOWN]

    def test_suggestions_keyboard_has_a_rating_row(self):
        kb = build_suggestions_keyboard(_SUGGESTIONS)
        last_row = kb.inline_keyboard[-1]
        assert [btn.callback_data for btn in last_row] == [RATE_UP, RATE_DOWN]


class TestStripRatingRow:
    def test_removes_the_last_row(self):
        stripped = strip_rating_row(KEYBOARD)
        assert stripped.inline_keyboard == KEYBOARD.inline_keyboard[:-1]

    def test_removes_the_rating_row_from_a_suggestions_keyboard(self):
        kb = build_suggestions_keyboard(_SUGGESTIONS)
        stripped = strip_rating_row(kb)
        assert stripped.inline_keyboard == kb.inline_keyboard[:-1]


class TestBuildSuggestionsKeyboard:
    def test_one_button_row_per_suggestion_plus_rating_row(self):
        kb = build_suggestions_keyboard(_SUGGESTIONS)
        assert len(kb.inline_keyboard) == 3

    def test_button_label_includes_number_and_note(self):
        kb = build_suggestions_keyboard(_SUGGESTIONS)
        assert kb.inline_keyboard[0][0].text == "1 · warm"
        assert kb.inline_keyboard[1][0].text == "2 · playful"

    def test_callback_data_is_select_colon_index(self):
        kb = build_suggestions_keyboard(_SUGGESTIONS)
        assert kb.inline_keyboard[0][0].callback_data == "select:0"
        assert kb.inline_keyboard[1][0].callback_data == "select:1"
