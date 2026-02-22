import re
import logging
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes

logger = logging.getLogger(__name__)


class Handlers:
    def __init__(self, db):
        self.db = db

    def register(self, application):
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help))
        application.add_handler(CommandHandler("log", self.log_workout))
        application.add_handler(CommandHandler("stats", self.stats))
        application.add_handler(CommandHandler("history", self.history))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.echo))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        await self.db.get_or_create_user(user.id, user.username)
        await update.message.reply_text(
            f"Welcome {user.first_name}!\n\n"
            "I'm your workout tracking bot. Use /help to see commands."
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🏋️ *Workout Bot Commands*\n\n"
            "/start - Register\n"
            "/log <exercise> <sets>x<reps> <weight> - Log workout\n"
            "/stats - Your statistics\n"
            "/history - Recent workouts\n\n"
            "*Examples:*\n"
            "• /log bench press 3x10 60\n"
            "• /log squat 5x5 100\n"
            "• /log pull ups 3x12",
            parse_mode="Markdown"
        )

    async def log_workout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "Please provide workout details.\nExample: /log bench press 3x10 60"
            )
            return

        user = update.effective_user
        user_id = await self.db.get_or_create_user(user.id, user.username)

        text = " ".join(context.args)
        sets, reps, weight = self._parse_workout(text)
        exercise = self._extract_exercise(text)

        await self.db.add_workout(user_id, exercise, sets, reps, weight)

        response = f"✅ Logged: {exercise}"
        if sets and reps:
            response += f" - {sets}x{reps}"
        if weight:
            response += f" @ {weight}kg"

        await update.message.reply_text(response)

    def _parse_workout(self, text: str) -> tuple:
        sets = reps = weight = None

        match = re.search(r"(\d+)x(\d+)", text)
        if match:
            sets, reps = int(match.group(1)), int(match.group(2))

        text_clean = re.sub(r"\d+x\d+", "", text)
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg|lb)?$", text_clean)
        if match:
            weight = float(match.group(1))

        return sets, reps, weight

    def _extract_exercise(self, text: str) -> str:
        text = re.sub(r"\d+x\d+", "", text)
        text = re.sub(r"\d+(?:\.\d+)?\s*(?:kg|lb)?$", "", text)
        return text.strip()

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = await self.db.get_or_create_user(user.id, user.username)
        stats = await self.db.get_workout_stats(user_id)
        await update.message.reply_text(
            f"📊 *Your Statistics*\n\n"
            f"Total workouts: {stats['total_workouts']}\n"
            f"Unique exercises: {stats['unique_exercises']}",
            parse_mode="Markdown"
        )

    async def history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = await self.db.get_or_create_user(user.id, user.username)
        workouts = await self.db.get_user_workouts(user_id, 5)

        if not workouts:
            await update.message.reply_text("No workouts logged yet. Use /log to add one!")
            return

        lines = ["📋 *Recent Workouts*\n"]
        for w in workouts:
            exercise, sets, reps, weight, notes, created_at = w
            line = f"• {exercise}"
            if sets and reps:
                line += f" - {sets}x{reps}"
            if weight:
                line += f" @ {weight}kg"
            lines.append(line)

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "I received your message! Use /help to see available commands."
        )
