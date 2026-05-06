import logging

from loguru import logger
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from bot.config import TOKEN
from bot.handlers_v2 import handle_message as handle_message_v2
from bot.handlers_v2.keyboard import handle_button_click


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
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def main() -> None:
    logging.basicConfig(handlers=[_InterceptHandler()], level=logging.INFO, force=True)
    app = ApplicationBuilder().token(TOKEN).concurrent_updates(True).build()
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE,
            handle_message_v2,
        )
    )
    app.add_handler(CallbackQueryHandler(handle_button_click))
    app.run_polling(drop_pending_updates=True)  # Drop pending updates at startup


if __name__ == "__main__":
    main()
