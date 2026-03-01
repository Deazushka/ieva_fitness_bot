from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from keyboards import (
    get_history_inline_keyboard,
    get_history_reply_keyboard,
    get_main_menu
)
from database import (
    get_or_create_user,
    get_workouts_history,
    get_workouts_history_count,
    get_workout_details
)

HISTORY_MENU = 1
HISTORY_DETAIL = 2

async def start_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user_id = await get_or_create_user(user.id, user.username)
    context.user_data['db_user_id'] = db_user_id
    
    await show_history_page(update, context, page=1)
    
    # Reply Keyboard внизу, для возврата из всего меню истории
    await update.message.reply_text("Управление историей", reply_markup=get_history_reply_keyboard())
    return HISTORY_MENU

async def show_history_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1):
    db_user_id = context.user_data['db_user_id']
    count = await get_workouts_history_count(db_user_id)
    
    if count == 0:
        msg = "У вас пока нет завершенных тренировок."
        if update.callback_query:
            await update.callback_query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return
        
    per_page = 5
    workouts = await get_workouts_history(db_user_id, limit=per_page * 10, offset=0) # Грузим больше для пагинации в памяти или можно сделать LIMIT/OFFSET
    # Для простоты пагинации грузим порцию
    
    # Пересчитываем общее кол-во страниц
    total_pages = (count + per_page - 1) // per_page
    msg = f"📊 История тренировок (страница {page}/{total_pages})"
    
    markup = get_history_inline_keyboard(workouts, page=page, per_page=per_page)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(msg, reply_markup=markup)
    else:
        await update.message.reply_text(msg, reply_markup=markup)

async def history_inline_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data.startswith("hist_page_"):
         page = int(data.split("_")[-1])
         await show_history_page(update, context, page=page)
         return HISTORY_MENU
         
    if data.startswith("hist_"):
         workout_id = int(data.split("_")[-1])
         details = await get_workout_details(workout_id)
         
         if not details:
             await query.answer("Тренировка не найдена", show_alert=True)
             return HISTORY_MENU
             
         try:
              dt_str = details['started_at'][:16] # YYYY-MM-DD HH:MM
         except:
              dt_str = "Неизвестно"
              
         text = (
             f"📋 Тренировка: {dt_str}\n"
             f"Категория: {details['category_name']}\n\n"
             f"{details['sets_str']}"
         )
         
         await query.answer()
         # Показываем сообщение и оставляем кнопку "Назад" в ReplyKeyboard
         await context.bot.send_message(
             chat_id=update.effective_chat.id,
             text=text,
             reply_markup=get_history_reply_keyboard()
         )
         
         # Закрываем меню со списком
         await query.message.delete()
         
         return HISTORY_DETAIL

async def history_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔙 Назад":
        if context.user_data.get('history_state') == HISTORY_DETAIL:
            context.user_data['history_state'] = HISTORY_MENU
            await show_history_page(update, context, page=1)
            return HISTORY_MENU
        else:
             # Выход в главное меню
             await update.message.reply_text("Главное меню", reply_markup=get_main_menu())
             return ConversationHandler.END

def setup_history_handlers(application):
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📊 История$"), start_history)],
        states={
            HISTORY_MENU: [
                CallbackQueryHandler(history_inline_callback, pattern="^hist_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, history_reply_handler)
            ],
            HISTORY_DETAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, history_reply_handler)
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^🔙 Назад$"), history_reply_handler)],
        name="history_conversation"
    )
    application.add_handler(conv_handler)
