"""SettingsTrigger — handles /start and /settings commands and language selection callbacks."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.config.lang import SUPPORTED_TARGET_LANGUAGES
from bot.config.messages import MsgChooseLanguage, MsgLanguageSelected
from bot.keyboard import LANG_TARGET_PREFIX, build_language_keyboard
from bot.localizer import Localizer
from bot.session import UserSession


class SettingsTrigger:
    def __init__(self, localizer: Localizer) -> None:
        self._localizer = localizer

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        session = UserSession.from_context(context)
        keyboard = build_language_keyboard(SUPPORTED_TARGET_LANGUAGES)
        text = self._localizer.t(MsgChooseLanguage, session.base_language)
        await update.message.reply_text(text, reply_markup=keyboard)

    async def handle_language_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        await query.answer()

        language_code = query.data[len(LANG_TARGET_PREFIX):]
        session = UserSession.from_context(context)
        session.target_language = language_code

        from bot.config.lang import LANGUAGE_NAMES
        language_name = LANGUAGE_NAMES.get(language_code, language_code)
        text = self._localizer.t(MsgLanguageSelected, session.base_language, language=language_name)
        await query.message.reply_text(text)
