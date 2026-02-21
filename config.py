import os
import logging
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_PATH = os.getenv("DATABASE_PATH", "workout.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

if not TOKEN or TOKEN == "your_token_here":
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables. Please create .env file with your token.")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL, logging.INFO)
)

logger = logging.getLogger(__name__)
