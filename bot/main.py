import logging

from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters

from bot.config import TOKEN
from bot.handlers import handle_message, handle_button_click


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_button_click))
    app.run_polling()


if __name__ == "__main__":
    main()
