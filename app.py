import logging
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from src.bot import create_application, setup_webhook
from src.database import Database

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=os.getenv('LOG_LEVEL', 'INFO')
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

db = Database()
application = None


async def init_app():
    global application
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError('TELEGRAM_BOT_TOKEN environment variable is required')

    await db.connect()
    logger.info('Database connected')

    application = create_application(token, db)
    await application.initialize()
    await application.start()
    logger.info('Application initialized')

    render_url = os.getenv('RENDER_EXTERNAL_URL')
    if render_url:
        await setup_webhook(application, token, render_url)

    return application


@app.before_request
async def before_first_request():
    global application
    if application is None:
        await init_app()


@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        update = request.get_json(force=True)
        if application:
            application.update_queue.put(update)
        return jsonify({'status': 'ok'})
    return jsonify({'status': 'error'}), 400


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})


@app.route('/', methods=['GET'])
def index():
    return jsonify({'status': 'running', 'service': 'workout-bot'})


if __name__ == '__main__':
    import asyncio

    async def run():
        await init_app()
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)

    asyncio.run(run())
