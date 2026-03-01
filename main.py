import asyncio
import logging
from telegram.ext import Application
from config import TELEGRAM_BOT_TOKEN
from database import create_tables
from handlers.start import setup_start_handlers
from handlers.workout import setup_workout_handlers
from handlers.history import setup_history_handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def init_db():
    await create_tables()
    logger.info("База данных инициализирована.")


def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Токен бота не задан. Установите переменную окружения TELEGRAM_BOT_TOKEN.")
        return

    # Создаём event loop явно и оставляем его открытым (asyncio.run() закрывает loop после выполнения)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    setup_start_handlers(application)
    setup_workout_handlers(application)
    setup_history_handlers(application)

    from telegram import Update
    from telegram.ext import ContextTypes, MessageHandler, filters
    from keyboards import get_main_menu

    async def settings_dummy(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Настройки пока в разработке.", reply_markup=get_main_menu())

    application.add_handler(MessageHandler(filters.Regex("^⚙️ Настройки$"), settings_dummy))

    logger.info("Бот запущен. Ожидание сообщений...")
    # run_polling() использует открытый event loop через asyncio.get_event_loop()
    application.run_polling()


if __name__ == '__main__':
    main()
