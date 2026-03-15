import logging

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from bot.config import TOKEN
from bot.handlers import handle_button_click, handle_message
from bot.handlers_v2 import handle_message as handle_message_v2

def main() -> None:
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).concurrent_updates(True).build()
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE,
            handle_message_v2,
        )
    )
    # app.add_handler(CallbackQueryHandler(handle_button_click))
    app.run_polling(drop_pending_updates=True)  # Drop pending updates at startup


if __name__ == "__main__":
    main()
