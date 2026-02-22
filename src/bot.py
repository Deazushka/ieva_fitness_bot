import logging
from telegram import Bot
from telegram.ext import Application, ApplicationBuilder

from .handlers import Handlers

logger = logging.getLogger(__name__)


def create_bot(token: str) -> Bot:
    return Bot(token=token)


def create_application(token: str) -> Application:
    application = (
        ApplicationBuilder()
        .token(token)
        .build()
    )
    
    handlers = Handlers()
    handlers.register(application)
    
    logger.info('Application created with all handlers registered')
    
    return application
