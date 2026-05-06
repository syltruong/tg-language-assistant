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
    def test_format_returns_result_unchanged(self):
        action = CorrectAction(localizer=_LOCALIZER, prompt_template="")
        assert action.format("Bonjour monde!", _LP) == "Bonjour monde!"

    def test_parse_returns_raw_string(self):
        action = CorrectAction(localizer=_LOCALIZER, prompt_template="")
        assert action.parse("Bonjour monde!") == "Bonjour monde!"


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


class TestRephraseAction:
    def test_format_renders_bullet_list(self):
        from bot.actions.verbs.rephrase import RephraseAction

        action = RephraseAction(localizer=_LOCALIZER, prompt_template="")
        result = action.format(
            [
                {"rephrasing": "C'est super", "note": "casual"},
                {"rephrasing": "C'est excellent", "note": "formal"},
            ],
            _LP,
        )
        assert "C'est super" in result
        assert "casual" in result
        assert "C'est excellent" in result

    def test_format_renders_notes_in_italics(self):
        action = RephraseAction(localizer=_LOCALIZER, prompt_template="")
        result = action.format([{"rephrasing": "Salut", "note": "informal"}], _LP)
        assert "<i>(informal)</i>" in result

    def test_parse_returns_list_for_valid_json(self):
        action = RephraseAction(localizer=_LOCALIZER, prompt_template="")
        result = action.parse('[{"rephrasing": "Salut", "note": "casual"}]')
        assert result == [{"rephrasing": "Salut", "note": "casual"}]

    def test_parse_raises_for_malformed_json(self):
        import pytest

        action = RephraseAction(localizer=_LOCALIZER, prompt_template="")
        with pytest.raises(ValueError):
            action.parse("not json")

    def test_parse_raises_when_not_a_list(self):
        import pytest

        action = RephraseAction(localizer=_LOCALIZER, prompt_template="")
        with pytest.raises(ValueError):
            action.parse('{"rephrasing": "Salut"}')


class TestReplyAction:
    def test_format_renders_bullet_list(self):
        from bot.actions.verbs.reply import ReplyAction

        action = ReplyAction(localizer=_LOCALIZER, prompt_template="")
        result = action.format(
            [
                {"reply": "Bien sûr !", "tone": "warm"},
                {"reply": "Peut-être.", "tone": "reserved"},
            ],
            _LP,
        )
        assert "Bien sûr !" in result
        assert "warm" in result

    def test_format_renders_tone_in_italics(self):
        action = ReplyAction(localizer=_LOCALIZER, prompt_template="")
        result = action.format([{"reply": "Non.", "tone": "direct"}], _LP)
        assert "<i>(direct)</i>" in result

    def test_parse_returns_list_for_valid_json(self):
        action = ReplyAction(localizer=_LOCALIZER, prompt_template="")
        result = action.parse('[{"reply": "Oui", "tone": "warm"}]')
        assert result == [{"reply": "Oui", "tone": "warm"}]

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
