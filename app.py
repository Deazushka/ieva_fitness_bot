import asyncio
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
_initialized = False


def init_sync():
    global application, _initialized
    if _initialized:
        return
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error('TELEGRAM_BOT_TOKEN environment variable is required')
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    loop.run_until_complete(db.connect())
    logger.info('Database connected')

    application = create_application(token, db)
    loop.run_until_complete(application.initialize())
    loop.run_until_complete(application.start())
    logger.info('Application initialized')

    render_url = os.getenv('RENDER_EXTERNAL_URL')
    if render_url:
        loop.run_until_complete(setup_webhook(application, token, render_url))

    _initialized = True


init_sync()


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
    if not _initialized:
        return jsonify({'status': 'not initialized'}), 503
    return jsonify({'status': 'healthy'})


@app.route('/', methods=['GET'])
def index():
    return jsonify({'status': 'running', 'service': 'workout-bot'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
