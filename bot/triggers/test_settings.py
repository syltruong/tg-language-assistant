import pytest

from bot.config.lang import SUPPORTED_TARGET_LANGUAGES
from bot.keyboard import LANG_TARGET_PREFIX
from bot.localizer import Localizer
from bot.session import UserSession
from bot.triggers.settings import SettingsTrigger
from tests.factories import make_callback_update, make_context, make_update


def _make_trigger() -> SettingsTrigger:
    return SettingsTrigger(localizer=Localizer())


class TestSettingsTriggerStart:
    @pytest.mark.asyncio
    async def test_start_sends_message_with_language_keyboard(self):
        trigger = _make_trigger()
        update = make_update(text="/start")
        context = make_context()

        await trigger.handle(update, context)

        update.message.reply_text.assert_called_once()
        call_kwargs = update.message.reply_text.call_args.kwargs
        assert call_kwargs.get("reply_markup") is not None

    @pytest.mark.asyncio
    async def test_keyboard_has_one_button_per_supported_language(self):
        trigger = _make_trigger()
        update = make_update(text="/start")
        context = make_context()

        await trigger.handle(update, context)

        keyboard = update.message.reply_text.call_args.kwargs["reply_markup"]
        buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        assert len(buttons) == len(SUPPORTED_TARGET_LANGUAGES)

    @pytest.mark.asyncio
    async def test_keyboard_buttons_have_lang_target_prefix(self):
        trigger = _make_trigger()
        update = make_update(text="/start")
        context = make_context()

        await trigger.handle(update, context)

        keyboard = update.message.reply_text.call_args.kwargs["reply_markup"]
        buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        assert all(btn.callback_data.startswith(LANG_TARGET_PREFIX) for btn in buttons)


class TestSettingsTriggerSettings:
    @pytest.mark.asyncio
    async def test_settings_sends_same_language_keyboard_as_start(self):
        trigger = _make_trigger()
        start_update = make_update(text="/start")
        settings_update = make_update(text="/settings")
        context = make_context()

        await trigger.handle(start_update, context)
        await trigger.handle(settings_update, context)

        start_keyboard = start_update.message.reply_text.call_args.kwargs["reply_markup"]
        settings_keyboard = settings_update.message.reply_text.call_args.kwargs["reply_markup"]
        assert start_keyboard == settings_keyboard


class TestSettingsTriggerLanguageCallback:
    @pytest.mark.asyncio
    async def test_lang_target_callback_sets_session_target_language(self):
        trigger = _make_trigger()
        update = make_callback_update(callback_data="lang_target:fr")
        context = make_context()

        await trigger.handle_language_callback(update, context)

        session = UserSession.from_context(context)
        assert session.target_language == "fr"

    @pytest.mark.asyncio
    async def test_lang_target_callback_sends_confirmation_mentioning_language(self):
        trigger = _make_trigger()
        update = make_callback_update(callback_data="lang_target:fr")
        context = make_context()

        await trigger.handle_language_callback(update, context)

        update.callback_query.message.reply_text.assert_called_once()
        sent_text = update.callback_query.message.reply_text.call_args.args[0]
        assert "French" in sent_text
