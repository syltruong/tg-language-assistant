from bot.keyboard import build_suggestions_keyboard
from bot.types import Suggestion

_SUGGESTIONS = [
    Suggestion(text="Bien merci!", note="warm"),
    Suggestion(text="Oui, ça va!", note="playful"),
]


class TestBuildSuggestionsKeyboard:
    def test_one_button_row_per_suggestion(self):
        kb = build_suggestions_keyboard(_SUGGESTIONS)
        assert len(kb.inline_keyboard) == 2

    def test_button_label_includes_number_and_note(self):
        kb = build_suggestions_keyboard(_SUGGESTIONS)
        assert kb.inline_keyboard[0][0].text == "1 · warm"
        assert kb.inline_keyboard[1][0].text == "2 · playful"

    def test_callback_data_is_select_colon_index(self):
        kb = build_suggestions_keyboard(_SUGGESTIONS)
        assert kb.inline_keyboard[0][0].callback_data == "select:0"
        assert kb.inline_keyboard[1][0].callback_data == "select:1"
