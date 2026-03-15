"""Unit tests for the message handler."""

import json
from unittest.mock import AsyncMock, patch

from bot.config.messages import MsgUnknownLanguage, MsgWantToGoDeeper, t
from bot.handlers_v2.message import (
    _handle_message_in_target_language,
    handle_message,
)
from bot.routing.local import (
    MessageHasNoTextError,
    TextHasNoWrittenContentError,
    TextTooLongError,
)
from bot.session import UserSession
from tests.factories import make_context, make_update

# ── Happy path ───────────────────────────────────────────────────────


@patch(
    "bot.handlers_v2.message.get_completion",
    new_callable=AsyncMock,
    return_value=json.dumps({
        "translation": "Hello",
        "one_line_context": "Greeting.",
    }),
)
@patch("bot.handlers_v2.message.detect_language", return_value="fr")
@patch("bot.handlers_v2.message.filter_telegram_message")
class TestHandleMessageHappyPath:
    async def test_sends_typing_action(
        self, _mock_filter, _mock_detect, _mock_get_completion
    ):
        update = make_update("Bonjour")
        await handle_message(update, make_context())

        update.effective_chat.send_action.assert_called_once_with("typing")

    async def test_calls_filter_with_message(
        self, mock_filter, _mock_detect, _mock_get_completion
    ):
        update = make_update("Bonjour")
        await handle_message(update, make_context())

        mock_filter.assert_called_once_with(update)

    async def test_calls_detect_language(
        self, _mock_filter, mock_detect, _mock_get_completion
    ):
        update = make_update("Bonjour")
        await handle_message(update, make_context())

        mock_detect.assert_called_once()


# ── UserFacingError paths ────────────────────────────────────────────


class TestHandleMessageErrors:
    @patch(
        "bot.handlers_v2.message.filter_telegram_message",
        side_effect=TextTooLongError(),
    )
    async def test_too_long_replies_with_error(self, _mock_filter):
        update = make_update("a" * 501)
        await handle_message(update, make_context())

        update.message.reply_text.assert_called_once_with(t(TextTooLongError))

    @patch(
        "bot.handlers_v2.message.filter_telegram_message",
        side_effect=MessageHasNoTextError(),
    )
    async def test_no_text_replies_with_error(self, _mock_filter):
        update = make_update("")
        await handle_message(update, make_context())

        update.message.reply_text.assert_called_once_with(t(MessageHasNoTextError))

    @patch(
        "bot.handlers_v2.message.filter_telegram_message",
        side_effect=TextHasNoWrittenContentError(),
    )
    async def test_no_written_content_replies_with_error(self, _mock_filter):
        update = make_update("!!!")
        await handle_message(update, make_context())

        update.message.reply_text.assert_called_once_with(
            t(TextHasNoWrittenContentError),
        )

    @patch(
        "bot.handlers_v2.message.filter_telegram_message",
        side_effect=TextTooLongError(),
    )
    async def test_error_still_sends_typing(self, _mock_filter):
        update = make_update("a" * 501)
        await handle_message(update, make_context())

        update.effective_chat.send_action.assert_called_once_with("typing")

    @patch(
        "bot.handlers_v2.message.filter_telegram_message",
        side_effect=TextTooLongError(),
    )
    @patch("bot.handlers_v2.message.detect_language")
    async def test_error_skips_detect_language(self, mock_detect, _mock_filter):
        update = make_update("a" * 501)
        await handle_message(update, make_context())

        mock_detect.assert_not_called()


# ── Language branching ───────────────────────────────────────────────


@patch("bot.handlers_v2.message.filter_telegram_message")
class TestLanguageBranching:
    @patch(
        "bot.handlers_v2.message._handle_message_in_base_language",
        new_callable=AsyncMock,
    )
    @patch("bot.handlers_v2.message.detect_language", return_value="en")
    async def test_base_language_calls_ui_handler(
        self,
        _mock_detect,
        mock_base_handler,
        _mock_filter,
    ):
        update = make_update("Hello there")
        context = make_context()
        await handle_message(update, context)

        mock_base_handler.assert_called_once()
        _, _, session = mock_base_handler.call_args[0]
        assert session is not None
        assert isinstance(session, UserSession)
        assert session.base_language == "en"
        assert session.target_language == "fr"

    @patch(
        "bot.handlers_v2.message._handle_message_in_target_language",
        new_callable=AsyncMock,
    )
    @patch("bot.handlers_v2.message.detect_language", return_value="fr")
    async def test_target_language_calls_target_handler(
        self,
        _mock_detect,
        mock_target_handler,
        _mock_filter,
    ):
        update = make_update("Bonjour")
        context = make_context()
        await handle_message(update, context)

        mock_target_handler.assert_called_once()
        _, _, session = mock_target_handler.call_args[0]
        assert session is not None
        assert isinstance(session, UserSession)
        assert session.base_language == "en"
        assert session.target_language == "fr"

    @patch("bot.handlers_v2.message.detect_language", return_value="de")
    async def test_unknown_language_replies_with_error(
        self,
        _mock_detect,
        _mock_filter,
    ):
        update = make_update("Guten Tag")
        await handle_message(update, make_context())

        update.message.reply_text.assert_called_once_with(
            t(MsgUnknownLanguage),
        )


# ── _handle_message_in_base_language ───────────────────────────────────


@patch("bot.handlers_v2.message.filter_telegram_message")
@patch("bot.handlers_v2.message.stream_completion")
@patch("bot.handlers_v2.message.stream_response", new_callable=AsyncMock)
class TestHandleMessageInBaseLanguage:
    async def test_calls_stream_response_with_reply(
        self,
        mock_stream_resp,
        mock_stream_comp,
        _mock_filter,
    ):
        update = make_update("Hello friend")
        context = make_context()
        await handle_message(update, context)

        mock_stream_resp.assert_called_once()

    @patch("bot.handlers_v2.message.detect_language", return_value="en")
    async def test_streams_translation_as_reply(
        self,
        _mock_detect,
        mock_stream_resp,
        _mock_stream_comp,
        _mock_filter,
    ):
        update = make_update("Hello friend")
        context = make_context()
        await handle_message(update, context)

        mock_stream_resp.assert_called_once()
        call_kwargs = mock_stream_resp.call_args
        assert call_kwargs.kwargs["reply_to_message_id"] == update.message.message_id
        assert call_kwargs.kwargs["chat_id"] == update.effective_chat.id

    @patch("bot.handlers_v2.message.detect_language", return_value="en")
    async def test_falls_back_to_send_response_on_stream_error(
        self,
        _mock_detect,
        mock_stream_resp,
        _mock_stream_comp,
        _mock_filter,
    ):
        mock_stream_resp.side_effect = Exception("stream broke")

        update = make_update("Hello friend")
        context = make_context()

        with (
            patch(
                "bot.handlers_v2.message.get_completion",
                new_callable=AsyncMock,
                return_value="Bonjour ami",
            ) as _mock_completion,
            patch(
                "bot.handlers_v2.message.send_response",
                new_callable=AsyncMock,
            ) as mock_send_resp,
        ):
            await handle_message(update, context)

            mock_send_resp.assert_called_once()
            call_kwargs = mock_send_resp.call_args.kwargs
            assert call_kwargs["text"] == "Bonjour ami"
            assert call_kwargs["reply_to_message_id"] == update.message.message_id


# ── _handle_message_in_target_language ───────────────────────────────────────


@patch("bot.handlers_v2.message.send_response", new_callable=AsyncMock)
@patch("bot.handlers_v2.message.get_completion", new_callable=AsyncMock)
class TestHandleMessageInTargetLanguage:
    async def test_calls_get_completion_with_translate_with_context_prompt(
        self,
        mock_get_completion,
        _mock_send_response,
    ):
        mock_get_completion.return_value = json.dumps({
            "translation": "Hello, how are you?",
            "one_line_context": "Common greeting.",
        })
        update = make_update("Bonjour")
        context = make_context()
        session = UserSession.from_context(context)

        await _handle_message_in_target_language(update, context, session)

        mock_get_completion.assert_called_once()
        kwargs = mock_get_completion.call_args.kwargs
        assert "English" in kwargs["system_prompt"]
        assert "French" in kwargs["system_prompt"]
        assert "Bonjour" in kwargs["user_prompt"]
        assert "French" in kwargs["user_prompt"]
        assert "English" in kwargs["user_prompt"]

    async def test_replies_with_formatted_translation_and_context(
        self,
        mock_get_completion,
        mock_send_response,
    ):
        translation = "Hello, how are you?"
        one_line_context = "Common casual greeting."
        mock_get_completion.return_value = json.dumps({
            "translation": translation,
            "one_line_context": one_line_context,
        })
        update = make_update("Bonjour")
        update.message.message_id = 1001
        context = make_context()
        session = UserSession.from_context(context)

        await _handle_message_in_target_language(update, context, session)

        mock_send_response.assert_called_once()
        call_kwargs = mock_send_response.call_args.kwargs
        body = call_kwargs["text"]
        assert call_kwargs["parse_mode"] == "HTML"
        assert "<blockquote>" in body
        assert translation in body
        assert "👉" in body
        assert "<i>" in body
        assert one_line_context in body
        assert t(MsgWantToGoDeeper) in body

    async def test_reply_to_message_id_set(
        self,
        mock_get_completion,
        mock_send_response,
    ):
        mock_get_completion.return_value = json.dumps({
            "translation": "Hi",
            "one_line_context": "Greeting.",
        })
        update = make_update("Salut")
        update.message.message_id = 2002
        context = make_context()
        session = UserSession.from_context(context)

        await _handle_message_in_target_language(update, context, session)

        assert mock_send_response.call_args.kwargs["reply_to_message_id"] == 2002
