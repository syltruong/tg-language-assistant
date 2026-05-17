from bot.actions.verbs.analyze import AnalyzeAction
from bot.actions.verbs.base import LanguagePair
from bot.actions.verbs.correct import CorrectAction
from bot.actions.verbs.rephrase import RephraseAction
from bot.actions.verbs.reply import ReplyAction
from bot.actions.verbs.translate import TranslateAction
from bot.localizer import Localizer
from bot.types import ActionType

_LP = LanguagePair(base="en", target="fr")
_LOCALIZER = Localizer()


class TestTranslateAction:
    def test_format_returns_result_unchanged(self):
        action = TranslateAction(localizer=_LOCALIZER, prompt_template="")
        assert action.format("Bonjour", _LP) == "Bonjour"

    def test_parse_returns_raw_string(self):
        action = TranslateAction(localizer=_LOCALIZER, prompt_template="")
        assert action.parse("Bonjour") == "Bonjour"


class TestAnalyzeAction:
    def test_format_renders_vocabulary_section(self):
        from bot.actions.verbs.analyze import AnalyzeAction

        action = AnalyzeAction(localizer=_LOCALIZER, prompt_template="")
        result = action.format(
            {
                "vocabulary": [
                    {
                        "form_in_text": "tkt",
                        "definition": "don't worry",
                        "base_form": "t'inquiète",
                    }
                ],
                "grammar": [],
            },
            _LP,
        )
        assert "<b>Vocabulary</b>" in result
        assert "tkt" in result

    def test_format_renders_grammar_section(self):
        from bot.actions.verbs.analyze import AnalyzeAction

        action = AnalyzeAction(localizer=_LOCALIZER, prompt_template="")
        result = action.format(
            {
                "vocabulary": [],
                "grammar": [
                    {
                        "quote": "tu vas bien",
                        "structure": "inversion",
                        "explanation": "formal question form",
                    }
                ],
            },
            _LP,
        )
        assert "<b>Grammar</b>" in result
        assert "tu vas bien" in result


class TestCorrectAction:
    def test_parse_mode_is_html(self):
        action = CorrectAction(localizer=_LOCALIZER, prompt_template="")
        assert action.parse_mode == "HTML"

    def test_parse_returns_dict_for_valid_json(self):
        import json

        action = CorrectAction(localizer=_LOCALIZER, prompt_template="")
        payload = {"corrected": "Je suis allée.", "annotations": [{"original": "allé", "correction": "allée", "explanation": "Gender agreement."}]}
        result = action.parse(json.dumps(payload))
        assert result == payload

    def test_parse_raises_for_malformed_json(self):
        import pytest

        action = CorrectAction(localizer=_LOCALIZER, prompt_template="")
        with pytest.raises(ValueError):
            action.parse("not json")

    def test_parse_raises_when_corrected_missing(self):
        import json

        import pytest

        action = CorrectAction(localizer=_LOCALIZER, prompt_template="")
        with pytest.raises(ValueError):
            action.parse(json.dumps({"annotations": []}))

    def test_parse_raises_when_annotations_missing(self):
        import json

        import pytest

        action = CorrectAction(localizer=_LOCALIZER, prompt_template="")
        with pytest.raises(ValueError):
            action.parse(json.dumps({"corrected": "Bien."}))

    def test_annotation_keys_all_present_in_prompt_template(self):
        import os

        from bot.actions.verbs.correct import _ANNOTATION_KEYS

        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "correct.md")
        with open(prompt_path, encoding="utf-8") as f:
            prompt = f.read()
        for key in _ANNOTATION_KEYS:
            assert key in prompt, f"Annotation key '{key}' missing from correct.md"

    def test_parse_raises_when_annotation_missing_field(self):
        import json

        import pytest

        action = CorrectAction(localizer=_LOCALIZER, prompt_template="")
        with pytest.raises(ValueError):
            action.parse(json.dumps({"corrected": "Bien.", "annotations": [{"original": "x", "correction": "y"}]}))

    def test_format_with_annotations_renders_corrected_and_diffs(self):
        action = CorrectAction(localizer=_LOCALIZER, prompt_template="")
        data = {
            "corrected": "Je suis allée.",
            "annotations": [{"original": "allé", "correction": "allée", "explanation": "Gender agreement."}],
        }
        result = action.format(data, _LP)
        assert "Je suis allée." in result
        assert "<s>allé</s>" in result
        assert "<b>allée</b>" in result
        assert "<i>Gender agreement.</i>" in result

    def test_format_with_empty_annotations_renders_no_corrections_message(self):
        action = CorrectAction(localizer=_LOCALIZER, prompt_template="")
        data = {"corrected": "Je suis allée.", "annotations": []}
        result = action.format(data, _LP)
        assert "No corrections needed." in result
        assert "Je suis allée." in result
        assert "<b>No corrections needed.</b>" in result

    def test_format_html_escapes_user_content(self):
        action = CorrectAction(localizer=_LOCALIZER, prompt_template="")
        data = {
            "corrected": "<b>safe</b>",
            "annotations": [{"original": "<x>", "correction": "&amp;", "explanation": "test>"}],
        }
        result = action.format(data, _LP)
        assert "<b>safe</b>" not in result or result.count("<b>") == 1  # only our own bold tag
        assert "&lt;x&gt;" in result
        assert "&amp;amp;" in result
        assert "test&gt;" in result


class TestAnalyzeActionParse:
    def test_parse_returns_dict_for_valid_json(self):
        action = AnalyzeAction(localizer=_LOCALIZER, prompt_template="")
        result = action.parse('{"vocabulary": [], "grammar": []}')
        assert result == {"vocabulary": [], "grammar": []}

    def test_parse_raises_for_malformed_json(self):
        import pytest

        action = AnalyzeAction(localizer=_LOCALIZER, prompt_template="")
        with pytest.raises(ValueError):
            action.parse("not json")

    def test_parse_raises_when_required_key_missing(self):
        import pytest

        action = AnalyzeAction(localizer=_LOCALIZER, prompt_template="")
        with pytest.raises(ValueError):
            action.parse('{"vocabulary": []}')


class TestSuggestionType:
    def test_suggestion_can_be_constructed_with_text_and_note(self):
        from bot.types import Suggestion

        s = Suggestion(text="Bien merci!", note="warm")
        assert s.text == "Bien merci!"
        assert s.note == "warm"

    def test_suggestion_note_defaults_to_empty_string(self):
        from bot.types import Suggestion

        s = Suggestion(text="Bien merci!")
        assert s.note == ""


class TestRephraseAction:
    def test_format_renders_bullet_list(self):
        from bot.actions.verbs.rephrase import RephraseAction
        from bot.types import Suggestion

        action = RephraseAction(localizer=_LOCALIZER, prompt_template="")
        result = action.format(
            [
                Suggestion(text="C'est super", note="casual"),
                Suggestion(text="C'est excellent", note="formal"),
            ],
            _LP,
        )
        assert "C'est super" in result
        assert "casual" in result
        assert "C'est excellent" in result

    def test_format_renders_note_in_italics(self):
        from bot.types import Suggestion

        action = RephraseAction(localizer=_LOCALIZER, prompt_template="")
        result = action.format([Suggestion(text="Salut", note="informal")], _LP)
        assert "<i>(informal)</i>" in result

    def test_parse_returns_list_of_suggestions_for_valid_json(self):
        from bot.types import Suggestion

        action = RephraseAction(localizer=_LOCALIZER, prompt_template="")
        result = action.parse('[{"text": "Salut", "note": "casual"}]')
        assert result == [Suggestion(text="Salut", note="casual")]

    def test_parse_raises_for_malformed_json(self):
        import pytest

        action = RephraseAction(localizer=_LOCALIZER, prompt_template="")
        with pytest.raises(ValueError):
            action.parse("not json")

    def test_parse_raises_when_not_a_list(self):
        import pytest

        action = RephraseAction(localizer=_LOCALIZER, prompt_template="")
        with pytest.raises(ValueError):
            action.parse('{"text": "Salut"}')

    def test_parse_raises_when_list_is_empty(self):
        import pytest

        action = RephraseAction(localizer=_LOCALIZER, prompt_template="")
        with pytest.raises(ValueError):
            action.parse("[]")

    def test_parse_raises_when_text_field_is_blank(self):
        import pytest

        action = RephraseAction(localizer=_LOCALIZER, prompt_template="")
        with pytest.raises(ValueError):
            action.parse('[{"text": "", "note": "casual"}]')

    def test_parse_accepts_blank_note(self):
        from bot.types import Suggestion

        action = RephraseAction(localizer=_LOCALIZER, prompt_template="")
        result = action.parse('[{"text": "C\'est super", "note": ""}]')
        assert result == [Suggestion(text="C'est super", note="")]


class TestReplyAction:
    def test_format_renders_bullet_list(self):
        from bot.actions.verbs.reply import ReplyAction
        from bot.types import Suggestion

        action = ReplyAction(localizer=_LOCALIZER, prompt_template="")
        result = action.format(
            [
                Suggestion(text="Bien sûr !", note="warm"),
                Suggestion(text="Peut-être.", note="reserved"),
            ],
            _LP,
        )
        assert "Bien sûr !" in result
        assert "warm" in result

    def test_format_renders_note_in_italics(self):
        from bot.types import Suggestion

        action = ReplyAction(localizer=_LOCALIZER, prompt_template="")
        result = action.format([Suggestion(text="Non.", note="direct")], _LP)
        assert "<i>(direct)</i>" in result

    def test_parse_returns_list_of_suggestions_for_valid_json(self):
        from bot.types import Suggestion

        action = ReplyAction(localizer=_LOCALIZER, prompt_template="")
        result = action.parse('[{"text": "Oui", "note": "warm"}]')
        assert result == [Suggestion(text="Oui", note="warm")]

    def test_parse_raises_for_malformed_json(self):
        import pytest

        action = ReplyAction(localizer=_LOCALIZER, prompt_template="")
        with pytest.raises(ValueError):
            action.parse("not json")

    def test_parse_raises_when_not_a_list(self):
        import pytest

        action = ReplyAction(localizer=_LOCALIZER, prompt_template="")
        with pytest.raises(ValueError):
            action.parse('{"reply": "Oui"}')

    def test_parse_raises_when_list_is_empty(self):
        import pytest

        action = ReplyAction(localizer=_LOCALIZER, prompt_template="")
        with pytest.raises(ValueError):
            action.parse("[]")

    def test_parse_raises_when_text_field_is_blank(self):
        import pytest

        action = ReplyAction(localizer=_LOCALIZER, prompt_template="")
        with pytest.raises(ValueError):
            action.parse('[{"text": "", "note": "warm"}]')

    def test_parse_raises_when_note_field_is_blank(self):
        import pytest

        action = ReplyAction(localizer=_LOCALIZER, prompt_template="")
        with pytest.raises(ValueError):
            action.parse('[{"text": "Bien merci!", "note": ""}]')


class TestActionRegistry:
    def _make_registry(self):
        from bot.actions.registry import ActionRegistry

        return ActionRegistry(localizer=_LOCALIZER)

    def test_get_translate_returns_translate_action(self):
        registry = self._make_registry()
        assert isinstance(registry.get(ActionType.TRANSLATE), TranslateAction)

    def test_get_analyze_returns_analyze_action(self):
        registry = self._make_registry()
        assert isinstance(registry.get(ActionType.ANALYZE), AnalyzeAction)

    def test_get_correct_returns_correct_action(self):
        registry = self._make_registry()
        assert isinstance(registry.get(ActionType.CORRECT), CorrectAction)

    def test_get_rephrase_returns_rephrase_action(self):
        registry = self._make_registry()
        assert isinstance(registry.get(ActionType.REPHRASE), RephraseAction)

    def test_get_reply_returns_reply_action(self):
        registry = self._make_registry()
        assert isinstance(registry.get(ActionType.REPLY), ReplyAction)

    def test_get_unknown_action_raises(self):
        import pytest

        registry = self._make_registry()
        with pytest.raises(KeyError):
            registry.get("nonexistent")
