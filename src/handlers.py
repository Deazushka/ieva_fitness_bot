import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from .database import Database

logger = logging.getLogger(__name__)


class Handlers:
    def __init__(self, db: Database = None):
        self.db = db or Database()

    def register(self, application: Application) -> None:
        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(CommandHandler('help', self.help))
        application.add_handler(CommandHandler('log', self.log_workout))
        application.add_handler(CommandHandler('stats', self.stats))
        application.add_handler(CommandHandler('history', self.history))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.db.connect()
        user = update.effective_user
        await self.db.get_or_create_user(user.id, user.username)
        
        await update.message.reply_text(
            f'Welcome {user.first_name}!\n\n'
            'I\'m your workout tracking bot. Use /help to see available commands.'
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        help_text = '''
🏋️ *Workout Bot Commands*

/start - Start the bot and register
/help - Show this help message
/log <exercise> <sets>x<reps> <weight> - Log a workout
  Example: /log bench press 3x10 60
/stats - View your workout statistics
/history - View your recent workouts

*Examples:*
• `/log squat 5x5 100`
• `/log pull ups 3x12`
• `/log running - ran 5km`
        '''
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def log_workout(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            await update.message.reply_text(
                'Please provide workout details.\n'
                'Example: /log bench press 3x10 60'
            )
            return

        user = update.effective_user
        user_id = await self.db.get_or_create_user(user.id, user.username)
        
        workout_text = ' '.join(context.args)
        
        sets, reps, weight = self._parse_workout(workout_text)
        exercise = self._extract_exercise(workout_text)
        
        workout_id = await self.db.add_workout(
            user_id=user_id,
            exercise=exercise,
            sets=sets,
            reps=reps,
            weight=weight
        )
        
        response = f'✅ Logged: {exercise}'
        if sets and reps:
            response += f' - {sets}x{reps}'
        if weight:
            response += f' @ {weight}kg'
        
        await update.message.reply_text(response)

    def _parse_workout(self, text: str) -> tuple:
        import re
        
        sets = reps = weight = None
        
        sets_reps_match = re.search(r'(\d+)x(\d+)', text)
        if sets_reps_match:
            sets = int(sets_reps_match.group(1))
            reps = int(sets_reps_match.group(2))
        
        text_without_sets_reps = re.sub(r'\d+x\d+', '', text)
        weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kg|lb)?$', text_without_sets_reps)
        if weight_match:
            weight = float(weight_match.group(1))
        
        return sets, reps, weight

    def _extract_exercise(self, text: str) -> str:
        import re
        
        text = re.sub(r'\d+x\d+', '', text)
        text = re.sub(r'\d+(?:\.\d+)?\s*(?:kg|lb)?$', '', text)
        return text.strip()

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        user_id = await self.db.get_or_create_user(user.id, user.username)
        
        stats = await self.db.get_workout_stats(user_id)
        
        await update.message.reply_text(
            f'📊 *Your Statistics*\n\n'
            f'Total workouts: {stats["total_workouts"]}\n'
            f'Unique exercises: {stats["unique_exercises"]}',
            parse_mode='Markdown'
        )

    async def history(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        user_id = await self.db.get_or_create_user(user.id, user.username)
        
        workouts = await self.db.get_user_workouts(user_id, limit=5)
        
        if not workouts:
            await update.message.reply_text('No workouts logged yet. Use /log to add one!')
            return
        
        response = '📋 *Recent Workouts*\n\n'
        for workout in workouts:
            exercise, sets, reps, weight, notes, created_at = workout
            line = f'• {exercise}'
            if sets and reps:
                line += f' - {sets}x{reps}'
            if weight:
                line += f' @ {weight}kg'
            response += line + '\n'
        
        await update.message.reply_text(response, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            'I received your message! Use /help to see available commands.'
        )
