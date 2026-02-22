import asyncio
import logging
import os
from dotenv import load_dotenv

from src.bot import create_bot, create_application


load_dotenv()


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=os.getenv('LOG_LEVEL', 'INFO')
)
logger = logging.getLogger(__name__)


async def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError('TELEGRAM_BOT_TOKEN environment variable is required')

    application = create_application(token)
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    logger.info('Bot started successfully')
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info('Shutting down...')
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


if __name__ == '__main__':
    asyncio.run(main())
