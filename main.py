import asyncio
import logging
import os
from telegram.ext import Application
from config import TELEGRAM_BOT_TOKEN
from database import create_tables
from handlers.start import setup_start_handlers
from handlers.workout import setup_workout_handlers
from handlers.history import setup_history_handlers

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def init_db():
    await create_tables()
    logger.info("База данных инициализирована.")


async def run_bot():
    await init_db()

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрация обработчиков
    setup_start_handlers(application)
    setup_workout_handlers(application)
    setup_history_handlers(application)

    # Регистрация заглушки для меню настроек
    from telegram import Update
    from telegram.ext import ContextTypes, MessageHandler, filters
    from keyboards import get_main_menu

    async def settings_dummy(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Настройки пока в разработке.", reply_markup=get_main_menu())

    application.add_handler(MessageHandler(filters.Regex("^⚙️ Настройки$"), settings_dummy))

    PORT = int(os.environ.get("PORT", "8443"))
    RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

    logger.info("Бот готов к запуску...")

    async with application:
        if RENDER_EXTERNAL_URL:
            logger.info(f"Запуск Webhook на порту {PORT}, URL: {RENDER_EXTERNAL_URL}")
            await application.updater.start_webhook(
                listen="0.0.0.0",
                port=PORT,
                secret_token=os.environ.get("WEBHOOK_SECRET", "A-Secret-Token-12345"),
                webhook_url=f"{RENDER_EXTERNAL_URL}/webhook",
            )
            await application.start()
            await application.updater.idle()
        else:
            logger.info("Запуск Polling (локальный режим)...")
            await application.updater.start_polling()
            await application.start()
            await application.updater.idle()

        await application.stop()


def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Токен бота не задан. Установите переменную окружения TELEGRAM_BOT_TOKEN.")
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_bot())
    finally:
        loop.close()


if __name__ == '__main__':
    main()
