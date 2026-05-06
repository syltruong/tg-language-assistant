import logging

from loguru import logger
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from bot.config import TOKEN
from bot.handlers_v2.keyboard import KeyboardHandlerService
from bot.handlers_v2.message import MessageHandlerService
from bot.user_repository import SqliteUserRepository


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

    repo = SqliteUserRepository.from_env()
    message_service = MessageHandlerService(repo)
    keyboard_service = KeyboardHandlerService(repo)

    app = ApplicationBuilder().token(TOKEN).concurrent_updates(True).build()
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE,
            message_service.handle,
        )
    )
    app.add_handler(CallbackQueryHandler(keyboard_service.handle))
    app.run_polling(drop_pending_updates=True)  # Drop pending updates at startup


if __name__ == "__main__":
    main()
