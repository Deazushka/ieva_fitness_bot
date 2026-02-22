import logging
from telegram import Bot
from telegram.ext import Application, ApplicationBuilder

from .handlers import Handlers

logger = logging.getLogger(__name__)


def create_application(token: str, db) -> Application:
    application = (
        ApplicationBuilder()
        .token(token)
        .updater(None)
        .build()
    )

    handlers = Handlers(db)
    handlers.register(application)

    logger.info('Application created with all handlers registered')

    return application


async def setup_webhook(application: Application, token: str, base_url: str) -> None:
    webhook_url = f"{base_url}/webhook"
    bot = Bot(token=token)
    
    await bot.set_webhook(url=webhook_url)
    logger.info(f'Webhook set to: {webhook_url}')
