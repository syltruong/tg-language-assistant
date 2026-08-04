import logging
import os

from loguru import logger
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot.actions.registry import ActionRegistry
from bot.auth import AllowlistAuthorizer
from bot.config import ALLOWED_USERS, DB_PATH, MODEL_NAME, OPENAI_API_KEY, TOKEN
from bot.feedback import LangSmithFeedbackClient
from bot.gateway import LinguaLanguageDetector, MessageGateway
from bot.insights import SqliteInsightRepository
from bot.keyboard import LANG_TARGET_PREFIX, RATE_PREFIX, SAVE_PREFIX
from bot.llm_interface import LangGraphLLMClient, OpenAILLMClient
from bot.localizer import Localizer
from bot.publisher import ResponsePublisher
from bot.runner import ActionRunner
from bot.storage.db import Database
from bot.triggers.feedback import FeedbackTrigger
from bot.triggers.keyboard import KeyboardTrigger
from bot.triggers.message import MessageTrigger
from bot.triggers.save import SaveTrigger
from bot.triggers.saved_list import SavedListTrigger
from bot.triggers.settings import SettingsTrigger


def _load_system_prompt() -> str:
    path = os.path.join(os.path.dirname(__file__), "system.md")
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


class _InterceptHandler(logging.Handler):
    """Route stdlib logging records into loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno  # type: ignore[assignment]
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def main() -> None:
    logging.basicConfig(handlers=[_InterceptHandler()], level=logging.INFO, force=True)

    database = Database(path=DB_PATH)

    async def connect_database(_app) -> None:
        await database.connect()
        logger.info("Database ready at {}", DB_PATH)

    async def close_database(_app) -> None:
        await database.close()

    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .concurrent_updates(True)
        .post_init(connect_database)
        .post_shutdown(close_database)
        .build()
    )

    localizer = Localizer()
    authorizer = AllowlistAuthorizer(allowlist=ALLOWED_USERS)
    language_detector = LinguaLanguageDetector()
    gateway = MessageGateway(authorizer=authorizer, language_detector=language_detector)
    registry = ActionRegistry(localizer=localizer)
    llm = LangGraphLLMClient(inner=OpenAILLMClient(api_key=OPENAI_API_KEY, model=MODEL_NAME))
    runner = ActionRunner(llm=llm, system_prompt_template=_load_system_prompt())
    publisher = ResponsePublisher(bot=app.bot)

    message_trigger = MessageTrigger(
        gateway=gateway,
        registry=registry,
        runner=runner,
        publisher=publisher,
        localizer=localizer,
    )
    keyboard_trigger = KeyboardTrigger(
        registry=registry,
        runner=runner,
        publisher=publisher,
    )
    settings_trigger = SettingsTrigger(localizer=localizer)
    feedback_trigger = FeedbackTrigger(feedback_client=LangSmithFeedbackClient())
    insight_repository = SqliteInsightRepository(database=database)
    save_trigger = SaveTrigger(repository=insight_repository)
    saved_list_trigger = SavedListTrigger(
        repository=insight_repository, localizer=localizer
    )

    app.add_handler(CommandHandler("start", settings_trigger.handle))
    app.add_handler(CommandHandler("settings", settings_trigger.handle))
    app.add_handler(CommandHandler("saved", saved_list_trigger.handle))
    app.add_handler(
        CallbackQueryHandler(
            settings_trigger.handle_language_callback,
            pattern=f"^{LANG_TARGET_PREFIX}",
        )
    )
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE,
            message_trigger.handle,
        )
    )
    # Must be registered before the catch-all keyboard handler below, otherwise
    # rate:* callback data reaches KeyboardTrigger and raises a KeyError.
    app.add_handler(
        CallbackQueryHandler(feedback_trigger.handle, pattern=f"^{RATE_PREFIX}")
    )
    app.add_handler(
        CallbackQueryHandler(save_trigger.handle, pattern=f"^{SAVE_PREFIX}")
    )
    app.add_handler(CallbackQueryHandler(keyboard_trigger.handle))
    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        port = int(os.getenv("PORT", "8443"))
        logger.info("Starting in webhook mode: url={} port={}", webhook_url, port)
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path="/webhook",
            webhook_url=webhook_url,
            drop_pending_updates=True,
        )
    else:
        logger.info("Starting in polling mode")
        app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
