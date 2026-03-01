import asyncio
import logging
import os
from aiohttp import web
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


async def health_handler(request):
    return web.Response(text="OK")


async def run_http_server(port: int):
    """Минимальный HTTP сервер для удовлетворения требования Render по открытому порту."""
    app = web.Application()
    app.router.add_get("/", health_handler)
    app.router.add_get("/health", health_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health-check HTTP сервер запущен на порту {port}")


async def run_bot(application):
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    logger.info("Бот запущен. Ожидание сообщений...")
    # Ждём вечно — бот работает в фоне
    await asyncio.Event().wait()


async def main_async():
    await init_db()

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

    PORT = int(os.environ.get("PORT", "8080"))

    # Запускаем HTTP сервер и бота параллельно
    await asyncio.gather(
        run_http_server(PORT),
        run_bot(application),
    )


def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Токен бота не задан. Установите переменную окружения TELEGRAM_BOT_TOKEN.")
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main_async())
    finally:
        loop.close()


if __name__ == '__main__':
    main()
