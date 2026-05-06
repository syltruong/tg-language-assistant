"""Unit tests for the keyboard handler."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers_v2.keyboard import (
    BUTTON_ACTIONS,
    BUTTON_TITLES,
    KEYBOARD,
    _handle_analyze,
    handle_button_click,
)
from bot.session import UserSession
from bot.types import KeyboardActionType
from tests.factories import make_callback_update, make_context

# ── KEYBOARD structure ─────────────────────────────────────────────────────


class TestKeyboardStructure:
    def test_keyboard_has_two_rows(self):
        assert len(KEYBOARD.inline_keyboard) == 2

    def test_each_row_has_two_buttons(self):
        for row in KEYBOARD.inline_keyboard:
            assert len(row) == 2

    def test_callback_data_matches_keyboard_action_types(self):
        flat = [btn.callback_data for row in KEYBOARD.inline_keyboard for btn in row]
        assert set(flat) == {
            KeyboardActionType.ANALYZE,
            KeyboardActionType.CORRECT,
            KeyboardActionType.REPHRASE,
            KeyboardActionType.REPLY,
        }

    def test_button_titles_match_action_titles(self):
        for row in KEYBOARD.inline_keyboard:
            for btn in row:
                assert btn.text == BUTTON_TITLES[btn.callback_data]


class TestActionTitles:
    def test_has_entry_for_each_keyboard_action_type(self):
        for action in KeyboardActionType:
            assert action in BUTTON_TITLES
            assert isinstance(BUTTON_TITLES[action], str)
            assert len(BUTTON_TITLES[action]) > 0

    def test_button_actions_list_has_four_items(self):
        assert len(BUTTON_ACTIONS) == 4
        assert set(BUTTON_ACTIONS) == set(KeyboardActionType)


# ── handle_button_click ─────────────────────────────────────────────────────


@patch("bot.handlers_v2.keyboard.send_response", new_callable=AsyncMock)
class TestHandleButtonClick:
    @patch(
        "bot.handlers_v2.keyboard.get_completion",
        new_callable=AsyncMock,
        return_value='{"vocabulary":[],"grammar":[]}',
    )
    async def test_calls_answer(self, _mock_get_completion, mock_send_response):
        update = make_callback_update(KeyboardActionType.ANALYZE, reply_text="Hello")
        context = make_context()

        await handle_button_click(update, context)

        update.callback_query.answer.assert_called_once_with()

    @patch(
        "bot.handlers_v2.keyboard.get_completion",
        new_callable=AsyncMock,
        return_value='{"vocabulary":[],"grammar":[]}',
    )
    async def test_removes_keyboard_to_prevent_double_click(
        self, _mock_get_completion, mock_send_response
    ):
        update = make_callback_update(KeyboardActionType.CORRECT, reply_text="Hi")
        context = make_context()

        await handle_button_click(update, context)

        update.callback_query.edit_message_reply_markup.assert_called_once_with(
            reply_markup=None,
        )

    @pytest.mark.parametrize(
        ("callback_data", "expected_text"),
        [
            (KeyboardActionType.ANALYZE, "Analyzing..."),
            (KeyboardActionType.CORRECT, "Correcting..."),
            (KeyboardActionType.REPHRASE, "Rephrasing..."),
            (KeyboardActionType.REPLY, "Generating replies..."),
        ],
    )
    @patch(
        "bot.handlers_v2.keyboard.get_completion",
        new_callable=AsyncMock,
        return_value='{"vocabulary":[],"grammar":[]}',
    )
    async def test_dispatches_to_handler_and_sends_placeholder(
        self, _mock_get_completion, mock_send_response, callback_data, expected_text
    ):
        update = make_callback_update(callback_data, reply_text="Message to process")
        update.callback_query.message.message_id = 999
        update.callback_query.message.chat.id = 111
        context = make_context()

        await handle_button_click(update, context)

        mock_send_response.assert_called_once()
        call_kwargs = mock_send_response.call_args.kwargs
        assert call_kwargs["text"] == expected_text
        assert call_kwargs["chat_id"] == 111
        assert call_kwargs["reply_to_message_id"] == 999

    async def test_no_reply_text_sends_error_and_does_not_call_handler(
        self, mock_send_response
    ):
        update = make_callback_update(KeyboardActionType.ANALYZE)  # no reply_text
        context = make_context()

        await handle_button_click(update, context)

        mock_send_response.assert_called_once()
        assert "could not be accessed" in mock_send_response.call_args.kwargs["text"]

    async def test_unknown_callback_data_does_not_call_send_response(
        self, mock_send_response
    ):
        update = make_callback_update("unknown_action")
        context = make_context()

        await handle_button_click(update, context)

        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_reply_markup.assert_called_once()
        mock_send_response.assert_not_called()


# ── _handle_analyze ─────────────────────────────────────────────────────────


@patch("bot.handlers_v2.keyboard.get_completion", new_callable=AsyncMock)
@patch("bot.handlers_v2.keyboard.send_response", new_callable=AsyncMock)
class TestHandleAnalyze:
    def _make_mocks(self, send_response_mock, chat_id=111, message_id=999):
        update = make_callback_update(KeyboardActionType.ANALYZE, reply_text="Bonjour")
        update.callback_query.message.chat.id = chat_id
        update.callback_query.message.message_id = message_id
        sent_message = MagicMock()
        sent_message.message_id = 12345
        send_response_mock.return_value = sent_message
        context = make_context(
            user_data={"base_language": "en", "target_language": "fr"}
        )
        context.bot.edit_message_text = AsyncMock()
        session = UserSession.from_context(context)
        return update, context, session, sent_message

    async def test_calls_get_completion_with_prompts_containing_text_and_languages(
        self, mock_send_response, mock_get_completion
    ):
        mock_get_completion.return_value = '{"vocabulary":[],"grammar":[]}'
        update, context, session, _ = self._make_mocks(mock_send_response)

        await _handle_analyze(update.callback_query, context, session, "Bonjour")

        mock_get_completion.assert_called_once()
        call_kwargs = mock_get_completion.call_args.kwargs
        assert "English" in call_kwargs["system_prompt"]
        assert "French" in call_kwargs["system_prompt"]
        assert "Bonjour" in call_kwargs["user_prompt"]

    async def test_edits_message_with_formatted_result_when_completion_succeeds(
        self, mock_send_response, mock_get_completion
    ):
        mock_get_completion.return_value = json.dumps(
            {
                "vocabulary": [
                    {
                        "form_in_text": "tkt",
                        "base_form": "t'inquiète",
                        "definition": "don't worry",
                        "note": "IM shortcut",
                    },
                ],
                "grammar": [
                    {
                        "quote": "C'est parti",
                        "structure": "Presentative",
                        "explanation": "Idiomatic kick-off.",
                    },
                ],
            }
        )
        update, context, session, sent_message = self._make_mocks(mock_send_response)

        await _handle_analyze(
            update.callback_query, context, session, "tkt c'est parti"
        )

        context.bot.edit_message_text.assert_called_once()
        call_kwargs = context.bot.edit_message_text.call_args.kwargs
        assert call_kwargs["message_id"] == sent_message.message_id
        assert call_kwargs["chat_id"] == 111
        assert call_kwargs["parse_mode"] == "HTML"
        body = call_kwargs["text"]
        assert "<b>Vocabulary</b>" in body
        assert "tkt" in body
        assert "don't worry" in body
        assert "<b>Grammar</b>" in body
        assert "C'est parti" in body

    async def test_edits_message_with_error_fallback_when_get_completion_raises(
        self, mock_send_response, mock_get_completion
    ):
        mock_get_completion.side_effect = Exception("API error")
        update, context, session, _sent_message = self._make_mocks(mock_send_response)

        await _handle_analyze(update.callback_query, context, session, "Hello")

        context.bot.edit_message_text.assert_called_once()
        assert (
            "Analysis failed" in context.bot.edit_message_text.call_args.kwargs["text"]
        )

    async def test_send_response_called_first_then_edit_uses_returned_message_id(
        self, mock_send_response, mock_get_completion
    ):
        mock_get_completion.return_value = '{"vocabulary":[],"grammar":[]}'
        update, context, session, sent_message = self._make_mocks(mock_send_response)
        assert sent_message.message_id == 12345

        await _handle_analyze(update.callback_query, context, session, "Hi")

        mock_send_response.assert_called_once()
        assert mock_send_response.call_args.kwargs["text"] == "Analyzing..."
        context.bot.edit_message_text.assert_called_once_with(
            chat_id=111,
            message_id=12345,
            text="No vocabulary or grammar points for this text.",
            parse_mode="HTML",
        )
