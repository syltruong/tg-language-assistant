import logging

from loguru import logger
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from bot.config import MODEL_NAME, OPENAI_API_KEY, TOKEN
from bot.handlers_v2.keyboard import KeyboardHandlerService
from bot.handlers_v2.message import MessageHandlerService
from bot.llm import OpenAILLMClient


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

    llm = OpenAILLMClient(api_key=OPENAI_API_KEY, model=MODEL_NAME)
    msg_svc = MessageHandlerService(llm)
    kbd_svc = KeyboardHandlerService(llm)

    app = ApplicationBuilder().token(TOKEN).concurrent_updates(True).build()
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE,
            msg_svc.handle,
        )
    )
    app.add_handler(CallbackQueryHandler(kbd_svc.handle))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
