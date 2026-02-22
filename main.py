import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import ApplicationBuilder

from src.database import Database
from src.handlers import Handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=os.getenv("LOG_LEVEL", "INFO"),
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is required")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is required")

db = Database(DATABASE_URL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    logger.info("Database connected")

    ptb = ApplicationBuilder().token(TOKEN).updater(None).build()
    Handlers(db).register(ptb)

    await ptb.initialize()
    await ptb.start()
    logger.info("Bot started")

    webhook_url = f"{os.getenv('RENDER_EXTERNAL_URL')}/webhook"
    await ptb.bot.set_webhook(webhook_url)
    logger.info(f"Webhook set: {webhook_url}")

    app.state.ptb = ptb

    yield

    await ptb.stop()
    await ptb.shutdown()
    await db.disconnect()
    logger.info("Shutdown complete")


app = FastAPI(lifespan=lifespan)


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, app.state.ptb.bot)
    await app.state.ptb.process_update(update)
    return Response(status_code=200)


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/")
async def root():
    return {"status": "running", "service": "workout-bot"}
