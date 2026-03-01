from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from keyboards import get_main_menu
from database import get_or_create_user

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Регистрируем пользователя или получаем его id
    await get_or_create_user(user.id, user.username)
    
    await update.message.reply_text(
        "🏋️ Добро пожаловать!\nВыберите действие:",
        reply_markup=get_main_menu()
    )

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Этот бот поможет отслеживать ваши тренировки.\n\n"
        "• *Начать тренировку* — создать новую сессию, выбрать упражнения и записать подходы.\n"
        "• *История* — просмотреть предыдущие тренировки.\n\n"
        "Для навигации используйте кнопки внизу экрана."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

def setup_start_handlers(application):
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(MessageHandler(filters.Regex("^❓ Помощь$"), help_handler))
