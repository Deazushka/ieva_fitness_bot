import asyncio
import logging
import os
import threading
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from telegram import Update

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
_ptb_app = None
_event_loop = None


def run_async(coro):
    global _event_loop
    if _event_loop is None:
        return None
    future = asyncio.run_coroutine_threadsafe(coro, _event_loop)
    return future.result(timeout=30)


def event_loop_thread():
    global _event_loop, _ptb_app
    
    _event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_event_loop)
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error('TELEGRAM_BOT_TOKEN environment variable is required')
        return

    _event_loop.run_until_complete(db.connect())
    logger.info('Database connected')

    _ptb_app = create_application(token, db)
    _event_loop.run_until_complete(_ptb_app.initialize())
    _event_loop.run_until_complete(_ptb_app.start())
    logger.info('Application initialized')

    render_url = os.getenv('RENDER_EXTERNAL_URL')
    if render_url:
        _event_loop.run_until_complete(setup_webhook(_ptb_app, token, render_url))

    _event_loop.run_forever()


threading.Thread(target=event_loop_thread, daemon=True).start()


@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        update_data = request.get_json(force=True)
        logger.info(f'Received webhook update: {update_data}')
        
        if _ptb_app and _event_loop:
            update = Update.de_json(update_data, _ptb_app.bot)
            if update:
                logger.info(f'Processing update: {update.update_id}')
                try:
                    run_async(_ptb_app.process_update(update))
                    logger.info(f'Update {update.update_id} processed')
                except Exception as e:
                    logger.error(f'Error processing update: {e}')
            else:
                logger.warning('Failed to parse update')
        else:
            logger.warning('Application not initialized')
        
        return jsonify({'status': 'ok'})
    return jsonify({'status': 'error'}), 400


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})


@app.route('/', methods=['GET'])
def index():
    return jsonify({'status': 'running', 'service': 'workout-bot'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
