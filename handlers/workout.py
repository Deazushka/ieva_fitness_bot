import re
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from keyboards import (
    get_categories_keyboard,
    get_exercises_inline_keyboard,
    get_exercise_management_reply_keyboard,
    get_presets_keyboard,
    get_main_menu
)
from database import (
    get_or_create_user, get_categories, start_workout,
    get_active_workout, get_exercises, get_category_by_id,
    discard_active_workout, get_exercise_by_id, get_user_presets,
    save_set, finish_workout, get_workout_stats,
    add_category, delete_category, add_exercise, delete_exercise
)

# Состояния FSM
CATEGORY_SELECT = 1
EXERCISE_SELECT = 2
EXERCISE_DETAIL = 3
ADD_CATEGORY = 4
DELETE_CATEGORY = 5
ADD_EXERCISE = 6
DELETE_EXERCISE = 7

async def start_workout_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user_id = await get_or_create_user(user.id, user.username)
    context.user_data['db_user_id'] = db_user_id
    
    # Загружаем категории
    categories = await get_categories(db_user_id)
    
    await update.message.reply_text(
        "📋 Выберите категорию тренировки:",
        reply_markup=get_categories_keyboard(categories)
    )
    return CATEGORY_SELECT

async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    db_user_id = context.user_data.get('db_user_id')
    
    if text == "🔙 Назад":
        await update.message.reply_text("Отменено.", reply_markup=get_main_menu())
        return ConversationHandler.END
        
    if text == "➕ Добавить категорию":
        kb = ReplyKeyboardMarkup([["🔙 Отмена"]], resize_keyboard=True)
        await update.message.reply_text("Введите название новой категории:", reply_markup=kb)
        return ADD_CATEGORY
        
    if text == "🗑️ Удалить категорию":
        categories = await get_categories(db_user_id)
        custom_cats = [c for c in categories if c['user_id'] is not None]
        if not custom_cats:
            await update.message.reply_text("У вас нет созданных категорий для удаления.")
            return CATEGORY_SELECT
            
        kb = [[c['name']] for c in custom_cats]
        kb.append(["🔙 Отмена"])
        await update.message.reply_text("Выберите категорию для удаления:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return DELETE_CATEGORY

    categories = await get_categories(db_user_id)
    selected_cat = next((c for c in categories if c['name'] == text), None)
    
    if not selected_cat:
        await update.message.reply_text("Категория не найдена. Выберите из списка.")
        return CATEGORY_SELECT
        
    # Старт новой тренировки (со сбросом старой)
    workout_id = await start_workout(db_user_id, selected_cat['id'])
    context.user_data['workout_id'] = workout_id
    context.user_data['category_id'] = selected_cat['id']
    
    await show_exercises(update, context, selected_cat['name'], page=1)
    return EXERCISE_SELECT

async def show_exercises(update: Update, context: ContextTypes.DEFAULT_TYPE, cat_name: str, page: int = 1):
    db_user_id = context.user_data['db_user_id']
    cat_id = context.user_data['category_id']
    
    exercises = await get_exercises(cat_id, db_user_id)
    
    # Отправляем Reply клавиатуру сначала (с кнопками управления)
    msg_reply = "Управление тренировкой:"
    if update.callback_query:
        # Если перелистываем, Reply клавиатуру обновлять не нужно, только Inline
        await update.callback_query.answer()
        await update.callback_query.edit_message_reply_markup(
             reply_markup=get_exercises_inline_keyboard(exercises, page=page)
        )
    else:
        await update.message.reply_text(
            msg_reply,
            reply_markup=get_exercise_management_reply_keyboard()
        )
        await update.message.reply_text(
            f"💪 Категория: {cat_name}\nВыберите упражнение (страница {page}):",
            reply_markup=get_exercises_inline_keyboard(exercises, page=page)
        )

async def exercise_inline_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data.startswith("ex_sel_page_"):
        page = int(data.split("_")[-1])
        cat_id = context.user_data.get('category_id')
        cat = await get_category_by_id(cat_id)
        await show_exercises(update, context, cat['name'], page=page)
        return EXERCISE_SELECT
        
    if data.startswith("ex_sel_"):
        ex_id = int(data.split("_")[-1])
        exercise = await get_exercise_by_id(ex_id)
        if not exercise:
            await query.answer("Упражнение не найдено", show_alert=True)
            return EXERCISE_SELECT
            
        context.user_data['exercise_id'] = ex_id
        
        # Получаем пресеты
        db_user_id = context.user_data['db_user_id']
        presets = await get_user_presets(db_user_id, ex_id)
        
        await query.answer()
        
        # Удаляем предыдущее inline сообщение-меню для чистоты
        await query.message.delete()
        
        text = (
            f"💪 {exercise['name']}\n\n"
            "Введите подход:\n\n"
            "Формат:\nповторения [вес]\n\n"
            "Пример:\n12 50 (12 повторений с весом 50)\n"
            "15 (15 повторений без веса)"
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=get_presets_keyboard(presets)
        )
        return EXERCISE_DETAIL

async def exercise_management_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    db_user_id = context.user_data.get('db_user_id')
    
    if text == "🔙 Назад (к категориям)":
        categories = await get_categories(db_user_id)
        await update.message.reply_text(
            "📋 Выберите категорию тренировки:",
            reply_markup=get_categories_keyboard(categories)
        )
        return CATEGORY_SELECT
        
    if text == "❌ Отменить тренировку":
         await discard_active_workout(db_user_id)
         context.user_data.pop('workout_id', None)
         await update.message.reply_text("Тренировка отменена.", reply_markup=get_main_menu())
         return ConversationHandler.END
         
    if text == "✅ Завершить тренировку":
         workout_id = context.user_data.get('workout_id')
         if not workout_id:
             await update.message.reply_text("Активная тренировка не найдена.", reply_markup=get_main_menu())
             return ConversationHandler.END
             
         await finish_workout(workout_id)
         
         # Получение статистики
         cat_id = context.user_data.get('category_id')
         cat = await get_category_by_id(cat_id)
         total_ex, sets_str = await get_workout_stats(workout_id)
         
         summary = (
             f"✅ Тренировка завершена\n\n"
             f"Категория: {cat['name']}\n"
             f"Упражнений: {total_ex}\n\n"
             f"{sets_str}"
         )
         
         await update.message.reply_text(summary, reply_markup=get_main_menu())
         context.user_data.pop('workout_id', None)
         return ConversationHandler.END
         
    if text == "➕ Добавить упражнение":
        kb = ReplyKeyboardMarkup([["🔙 Отмена"]], resize_keyboard=True)
        await update.message.reply_text("Введите название нового упражнения:", reply_markup=kb)
        return ADD_EXERCISE
        
    if text == "🗑️ Удалить упражнение":
        cat_id = context.user_data['category_id']
        exercises = await get_exercises(cat_id, db_user_id)
        custom_exs = [e for e in exercises if e['user_id'] is not None]
        if not custom_exs:
             await update.message.reply_text("В этой категории нет ваших упражнений для удаления.")
             return EXERCISE_SELECT
             
        kb = [[e['name']] for e in custom_exs]
        kb.append(["🔙 Отмена"])
        await update.message.reply_text("Выберите упражнение для удаления:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return DELETE_EXERCISE

async def handle_add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    db_user_id = context.user_data.get('db_user_id')
    
    if text != "🔙 Отмена":
        await add_category(db_user_id, text)
        await update.message.reply_text(f"✅ Категория '{text}' добавлена.")
        
    categories = await get_categories(db_user_id)
    await update.message.reply_text("📋 Выберите категорию тренировки:", reply_markup=get_categories_keyboard(categories))
    return CATEGORY_SELECT

async def handle_delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    db_user_id = context.user_data.get('db_user_id')
    
    if text != "🔙 Отмена":
         await delete_category(db_user_id, text)
         await update.message.reply_text(f"✅ Категория '{text}' удалена.")
         
    categories = await get_categories(db_user_id)
    await update.message.reply_text("📋 Выберите категорию тренировки:", reply_markup=get_categories_keyboard(categories))
    return CATEGORY_SELECT

async def handle_add_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    db_user_id = context.user_data.get('db_user_id')
    cat_id = context.user_data.get('category_id')
    cat = await get_category_by_id(cat_id)
    
    if text != "🔙 Отмена":
        await add_exercise(cat_id, db_user_id, text)
        await update.message.reply_text(f"✅ Упражнение '{text}' добавлено.")
        
    await show_exercises(update, context, cat['name'], page=1)
    return EXERCISE_SELECT

async def handle_delete_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    db_user_id = context.user_data.get('db_user_id')
    cat_id = context.user_data.get('category_id')
    cat = await get_category_by_id(cat_id)
    
    if text != "🔙 Отмена":
        await delete_exercise(cat_id, db_user_id, text)
        await update.message.reply_text(f"✅ Упражнение '{text}' удалено.")
        
    await show_exercises(update, context, cat['name'], page=1)
    return EXERCISE_SELECT

async def save_set_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    db_user_id = context.user_data.get('db_user_id')
    workout_id = context.user_data.get('workout_id')
    ex_id = context.user_data.get('exercise_id')
    
    if text == "🔙 Назад (к упражнениям)":
        cat_id = context.user_data.get('category_id')
        cat = await get_category_by_id(cat_id)
        await show_exercises(update, context, cat['name'], page=1)
        return EXERCISE_SELECT
        
    # Разбор ввода (пресет или текст)
    # Форматы: "12", "12 50", "12 x 50" (если нажата кнопка)
    text = text.replace("x", "").strip()
    parts = re.split(r'\s+', text)
    
    try:
        reps = int(parts[0])
        weight = float(parts[1]) if len(parts) > 1 else None
        
        await save_set(workout_id, db_user_id, ex_id, reps, weight)
        
        w_str = f", {weight} кг" if weight else " (без веса)"
        msg = f"✅ Записано: {reps} повторений{w_str}."
        
        # Обновляем клавиатуру
        presets = await get_user_presets(db_user_id, ex_id)
        await update.message.reply_text(msg, reply_markup=get_presets_keyboard(presets))
        
    except ValueError:
         await update.message.reply_text("❌ Неверный формат. Попробуйте снова (например, '12 50' или '15').")
         
    return EXERCISE_DETAIL

def setup_workout_handlers(application):
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🏋️ Начать тренировку$"), start_workout_cmd)],
        states={
            CATEGORY_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, category_selected)],
            ADD_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_category)],
            DELETE_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_delete_category)],
            EXERCISE_SELECT: [
                CallbackQueryHandler(exercise_inline_callback, pattern="^ex_sel_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, exercise_management_reply)
            ],
            ADD_EXERCISE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_exercise)],
            DELETE_EXERCISE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_delete_exercise)],
            EXERCISE_DETAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_set_handler)]
        },
        fallbacks=[MessageHandler(filters.Regex("^🔙 Назад$"), category_selected)],
        name="workout_conversation"
    )
    application.add_handler(conv_handler)
