"""Unit tests for the keyboard handler."""

from unittest.mock import AsyncMock, patch

import pytest

from bot.handlers_v2.keyboard import (
    BUTTON_TITLES,
    BUTTON_ACTIONS,
    KEYBOARD,
    handle_button_click,
)
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
    async def test_calls_answer(self, mock_send_response):
        update = make_callback_update(KeyboardActionType.ANALYZE)
        context = make_context()

        await handle_button_click(update, context)

        update.callback_query.answer.assert_called_once_with()

    async def test_removes_keyboard_to_prevent_double_click(self, mock_send_response):
        update = make_callback_update(KeyboardActionType.CORRECT)
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
            (KeyboardActionType.REPLY, "Replies..."),
        ],
    )
    async def test_dispatches_to_handler_and_sends_placeholder(
        self, mock_send_response, callback_data, expected_text
    ):
        update = make_callback_update(callback_data)
        update.callback_query.message.message_id = 999
        update.callback_query.message.chat.id = 111
        context = make_context()

        await handle_button_click(update, context)

        mock_send_response.assert_called_once()
        call_kwargs = mock_send_response.call_args.kwargs
        assert call_kwargs["text"] == expected_text
        assert call_kwargs["chat_id"] == 111
        assert call_kwargs["reply_to_message_id"] == 999

    async def test_unknown_callback_data_does_not_call_send_response(
        self, mock_send_response
    ):
        update = make_callback_update("unknown_action")
        context = make_context()

        await handle_button_click(update, context)

        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_reply_markup.assert_called_once()
        mock_send_response.assert_not_called()
