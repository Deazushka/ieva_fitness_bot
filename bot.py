import re
import logging
import os
from datetime import datetime
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
from config import TOKEN, logger
from database import (
    get_categories, add_category, delete_category, get_exercises, add_exercise, delete_exercise,
    start_workout, add_exercise_to_workout, finish_workout, cancel_workout,
    get_user_workouts, get_workout_details, get_workout_stats,
    get_user_settings, update_user_settings, set_language, set_notifications,
    get_user_sets, add_user_set, delete_user_set, get_set_by_name
)
from constants import ConversationState, CallbackData, MESSAGES

active_workouts = {}

app = Flask(__name__)

@app.route('/')
def home():
    return "🏋️ Fitness Tracker Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

def get_user_language(user_id: int) -> str:
    try:
        settings = get_user_settings(user_id)
        return settings.get('language', 'ru')
    except:
        return 'ru'

def get_message(key: str, user_id: int, **kwargs) -> str:
    lang = get_user_language(user_id)
    return MESSAGES.get(lang, MESSAGES['ru']).get(key, key).format(**kwargs)

def create_main_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🏋️ Начать тренировку", callback_data=CallbackData.START_WORKOUT),
        ],
        [
            InlineKeyboardButton("📊 История", callback_data=CallbackData.HISTORY),
            InlineKeyboardButton("⚙️ Настройки", callback_data=CallbackData.SETTINGS),
        ],
        [
            InlineKeyboardButton("❓ Помощь", callback_data=CallbackData.HELP),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_categories_keyboard() -> InlineKeyboardMarkup:
    categories = get_categories()
    keyboard = []
    row = []
    for i, (cat_id, cat_name) in enumerate(categories):
        row.append(InlineKeyboardButton(f"• {cat_name}", callback_data=f"{CallbackData.CATEGORY_PREFIX}{cat_name}"))
        if len(row) == 2 or i == len(categories) - 1:
            keyboard.append(row)
            row = []
    
    keyboard.append([
        InlineKeyboardButton("➕ Добавить", callback_data=CallbackData.ADD_CATEGORY),
        InlineKeyboardButton("🗑️ Удалить", callback_data=CallbackData.DELETE_CATEGORY),
    ])
    keyboard.append([
        InlineKeyboardButton("🔙 Назад", callback_data=CallbackData.BACK),
    ])
    return InlineKeyboardMarkup(keyboard)

def create_delete_categories_keyboard() -> InlineKeyboardMarkup:
    categories = get_categories()
    keyboard = []
    row = []
    for i, (cat_id, cat_name) in enumerate(categories):
        row.append(InlineKeyboardButton(f"🗑️ {cat_name}", callback_data=f"del_cat_{cat_name}"))
        if len(row) == 2 or i == len(categories) - 1:
            keyboard.append(row)
            row = []
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=CallbackData.BACK)])
    return InlineKeyboardMarkup(keyboard)

def create_exercises_keyboard(category_name: str = None) -> InlineKeyboardMarkup:
    from database import get_exercises_by_category
    if category_name:
        exercises = get_exercises_by_category(category_name)
    else:
        exercises = get_exercises()
    keyboard = []
    row = []
    for i, ex_data in enumerate(exercises):
        if len(ex_data) == 3:
            ex_id, ex_name, cat_id = ex_data
        else:
            ex_id, ex_name = ex_data[0], ex_data[1]
        row.append(InlineKeyboardButton(f"• {ex_name}", callback_data=f"{CallbackData.EXERCISE_PREFIX}{ex_name}"))
        if len(row) == 2 or i == len(exercises) - 1:
            keyboard.append(row)
            row = []
    
    keyboard.append([
        InlineKeyboardButton("➕ Добавить", callback_data=CallbackData.ADD_EXERCISE),
        InlineKeyboardButton("🗑️ Удалить", callback_data=CallbackData.DELETE_EXERCISE),
    ])
    keyboard.append([
        InlineKeyboardButton("✅ Завершить", callback_data=CallbackData.FINISH_WORKOUT),
        InlineKeyboardButton("❌ Отмена", callback_data=CallbackData.CANCEL_WORKOUT),
    ])
    return InlineKeyboardMarkup(keyboard)

def create_delete_exercises_keyboard() -> InlineKeyboardMarkup:
    exercises = get_exercises()
    keyboard = []
    row = []
    for i, (ex_id, ex_name, cat_id) in enumerate(exercises):
        row.append(InlineKeyboardButton(f"🗑️ {ex_name}", callback_data=f"del_ex_{ex_name}"))
        if len(row) == 2 or i == len(exercises) - 1:
            keyboard.append(row)
            row = []
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=CallbackData.BACK)])
    return InlineKeyboardMarkup(keyboard)

def create_sets_keyboard(user_id: int) -> InlineKeyboardMarkup:
    user_sets = get_user_sets(user_id)
    keyboard = []
    row = []
    for i, (set_id, name, sets, reps, weight) in enumerate(user_sets):
        row.append(InlineKeyboardButton(f"📊 {name}", callback_data=f"{CallbackData.SET_PREFIX}{name}"))
        if len(row) == 2 or i == len(user_sets) - 1:
            keyboard.append(row)
            row = []
    
    keyboard.append([
        InlineKeyboardButton("➕ Добавить", callback_data=CallbackData.ADD_SET),
        InlineKeyboardButton("🗑️ Удалить", callback_data=CallbackData.DELETE_SET),
    ])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=CallbackData.BACK)])
    return InlineKeyboardMarkup(keyboard)

def create_delete_sets_keyboard(user_id: int) -> InlineKeyboardMarkup:
    user_sets = get_user_sets(user_id)
    keyboard = []
    row = []
    for i, (set_id, name, sets, reps, weight) in enumerate(user_sets):
        row.append(InlineKeyboardButton(f"🗑️ {name}", callback_data=f"del_set_{name}"))
        if len(row) == 2 or i == len(user_sets) - 1:
            keyboard.append(row)
            row = []
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=CallbackData.BACK)])
    return InlineKeyboardMarkup(keyboard)

def create_history_keyboard(workouts: list, page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    start = page * per_page
    end = start + per_page
    page_workouts = workouts[start:end]
    
    keyboard = []
    for workout in page_workouts:
        w_id, category, started, finished, total = workout
        date = datetime.fromisoformat(started).strftime("%d.%m.%Y %H:%M")
        keyboard.append([
            InlineKeyboardButton(
                f"📅 {date} - {category} ({total} упр.)",
                callback_data=f"{CallbackData.HISTORY_DETAIL_PREFIX}{w_id}"
            )
        ])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀ Назад", callback_data=f"{CallbackData.HISTORY_PAGE_PREFIX}{page-1}"))
    if end < len(workouts):
        nav_buttons.append(InlineKeyboardButton("Вперёд ▶", callback_data=f"{CallbackData.HISTORY_PAGE_PREFIX}{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data=CallbackData.BACK)])
    return InlineKeyboardMarkup(keyboard)

def create_settings_keyboard(user_id: int) -> InlineKeyboardMarkup:
    settings = get_user_settings(user_id)
    lang = settings.get('language', 'ru')
    units = settings.get('units', 'metric')
    notif = settings.get('notifications_enabled', False)
    
    keyboard = [
        [
            InlineKeyboardButton("🇷🇺 Русский" if lang != 'ru' else "✅ Русский", callback_data=f"{CallbackData.SETTINGS_LANGUAGE_PREFIX}ru"),
            InlineKeyboardButton("🇬🇧 English" if lang != 'en' else "✅ English", callback_data=f"{CallbackData.SETTINGS_LANGUAGE_PREFIX}en"),
        ],
        [
            InlineKeyboardButton("⚖️ Кг" if units != 'metric' else "✅ Кг", callback_data=f"{CallbackData.SETTINGS_UNITS_PREFIX}metric"),
            InlineKeyboardButton("⚖️ Фунты" if units != 'imperial' else "✅ Фунты", callback_data=f"{CallbackData.SETTINGS_UNITS_PREFIX}imperial"),
        ],
        [
            InlineKeyboardButton("🔔 Вкл" if not notif else "🔕 Выкл", callback_data=CallbackData.SETTINGS_NOTIFICATIONS),
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data=CallbackData.BACK),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def format_workout_summary(workout_id: int, user_id: int) -> str:
    details = get_workout_details(workout_id)
    if not details:
        return get_message('no_active_workout', user_id)
    
    workout = details['workout']
    exercises = details['exercises']
    
    category = workout[3]
    date = datetime.fromisoformat(workout[4]).strftime("%d.%m.%Y %H:%M")
    total = workout[6]
    
    exercises_text = ""
    for ex in exercises:
        ex_name, sets, reps, weight, _ = ex
        weight_str = f" ({weight} кг)" if weight else ""
        exercises_text += f"• {ex_name}: {sets}x{reps}{weight_str}\n"
    
    if not exercises_text:
        exercises_text = get_message('no_exercises', user_id)
    
    return get_message('workout_finished', user_id, 
                      category=category, total=total, 
                      exercises=exercises_text, date=date)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    await update.message.reply_text(
        get_message('start', user_id),
        reply_markup=create_main_menu_keyboard(user_id),
        parse_mode='Markdown'
    )
    return ConversationState.MAIN_MENU

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    if update.message:
        await update.message.reply_text(
            get_message('help', user_id),
            parse_mode='Markdown'
        )
    else:
        await update.callback_query.edit_message_text(
            get_message('help', user_id),
            reply_markup=create_main_menu_keyboard(user_id),
            parse_mode='Markdown'
        )
    return ConversationState.MAIN_MENU

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    
    if user_id in active_workouts:
        workout_id = active_workouts[user_id]['workout_id']
        cancel_workout(workout_id)
        del active_workouts[user_id]
        await update.message.reply_text(get_message('workout_cancelled', user_id))
    
    await update.message.reply_text(
        get_message('back_to_main', user_id),
        reply_markup=create_main_menu_keyboard(user_id)
    )
    return ConversationState.MAIN_MENU

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == CallbackData.START_WORKOUT:
        await query.edit_message_text(
            get_message('select_category', user_id),
            reply_markup=create_categories_keyboard()
        )
        return ConversationState.CATEGORY_SELECT
    
    elif data == CallbackData.HISTORY:
        workouts = get_user_workouts(user_id)
        if not workouts:
            await query.edit_message_text(
                get_message('history_empty', user_id),
                reply_markup=create_main_menu_keyboard(user_id)
            )
        else:
            stats = get_workout_stats(user_id)
            last = datetime.fromisoformat(stats['last_workout']).strftime("%d.%m.%Y") if stats['last_workout'] else "Нет"
            text = get_message('history_title', user_id, 
                             total=stats['total_workouts'],
                             exercises=stats['total_exercises'],
                             last=last)
            await query.edit_message_text(
                text,
                reply_markup=create_history_keyboard(workouts),
                parse_mode='Markdown'
            )
        return ConversationState.HISTORY_MENU
    
    elif data == CallbackData.SETTINGS:
        settings = get_user_settings(user_id)
        lang = "Русский" if settings['language'] == 'ru' else "English"
        units = "Кг" if settings['units'] == 'metric' else "Фунты"
        notif = "Вкл" if settings['notifications_enabled'] else "Выкл"
        
        await query.edit_message_text(
            get_message('settings_title', user_id, language=lang, units=units, notifications=notif),
            reply_markup=create_settings_keyboard(user_id),
            parse_mode='Markdown'
        )
        return ConversationState.SETTINGS_MENU
    
    elif data == CallbackData.HELP:
        return await help_command(update, context)
    
    return ConversationState.MAIN_MENU

async def category_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == CallbackData.BACK:
        await query.edit_message_text(
            get_message('start', user_id),
            reply_markup=create_main_menu_keyboard(user_id)
        )
        return ConversationState.MAIN_MENU
    
    elif data == CallbackData.ADD_CATEGORY:
        await query.edit_message_text(get_message('enter_category_name', user_id))
        return ConversationState.ADD_CATEGORY_NAME
    
    elif data == CallbackData.DELETE_CATEGORY:
        await query.edit_message_text(
            "🗑️ Выберите категорию для удаления:",
            reply_markup=create_delete_categories_keyboard()
        )
        return ConversationState.CATEGORY_SELECT
    
    elif data.startswith("del_cat_"):
        category_name = data[8:]
        if delete_category(category_name):
            await query.answer(f"✅ Категория '{category_name}' удалена")
            await query.edit_message_text(
                get_message('select_category', user_id),
                reply_markup=create_categories_keyboard()
            )
        else:
            await query.answer(f"❌ Не удалось удалить '{category_name}'")
        return ConversationState.CATEGORY_SELECT
    
    elif data.startswith(CallbackData.CATEGORY_PREFIX):
        category = data[len(CallbackData.CATEGORY_PREFIX):]
        username = query.from_user.username or query.from_user.first_name
        workout_id = start_workout(user_id, username, category)
        active_workouts[user_id] = {'workout_id': workout_id, 'category': category}
        
        await query.edit_message_text(
            get_message('workout_started', user_id, category=category),
            parse_mode='Markdown'
        )
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=get_message('select_exercise', user_id),
            reply_markup=create_exercises_keyboard(category)
        )
        return ConversationState.EXERCISE_SELECT
    
    return ConversationState.CATEGORY_SELECT

async def add_category_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    category_name = update.message.text.strip()
    
    add_category(category_name)
    await update.message.reply_text(get_message('category_added', user_id, name=category_name))
    
    await update.message.reply_text(
        get_message('select_category', user_id),
        reply_markup=create_categories_keyboard()
    )
    return ConversationState.CATEGORY_SELECT

async def exercise_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == CallbackData.ADD_EXERCISE:
        await query.edit_message_text(get_message('enter_exercise_name', user_id))
        return ConversationState.ADD_EXERCISE_NAME
    
    elif data == CallbackData.DELETE_EXERCISE:
        await query.edit_message_text(
            "🗑️ Выберите упражнение для удаления:",
            reply_markup=create_delete_exercises_keyboard()
        )
        return ConversationState.EXERCISE_SELECT
    
    elif data.startswith("del_ex_"):
        exercise_name = data[7:]
        if delete_exercise(exercise_name):
            await query.answer(f"✅ Упражнение '{exercise_name}' удалено")
            category = active_workouts.get(user_id, {}).get('category')
            await query.edit_message_text(
                get_message('select_exercise', user_id),
                reply_markup=create_exercises_keyboard(category)
            )
        else:
            await query.answer(f"❌ Не удалось удалить '{exercise_name}'")
        return ConversationState.EXERCISE_SELECT
    
    elif data == CallbackData.FINISH_WORKOUT:
        if user_id not in active_workouts:
            await query.edit_message_text(
                get_message('no_active_workout', user_id),
                reply_markup=create_main_menu_keyboard(user_id)
            )
            return ConversationState.MAIN_MENU
        
        workout_id = active_workouts[user_id]['workout_id']
        finish_workout(workout_id)
        summary = format_workout_summary(workout_id, user_id)
        del active_workouts[user_id]
        
        await query.edit_message_text(
            summary,
            reply_markup=create_main_menu_keyboard(user_id),
            parse_mode='Markdown'
        )
        return ConversationState.MAIN_MENU
    
    elif data == CallbackData.CANCEL_WORKOUT:
        if user_id in active_workouts:
            workout_id = active_workouts[user_id]['workout_id']
            cancel_workout(workout_id)
            del active_workouts[user_id]
        
        await query.edit_message_text(
            get_message('cancel_workout', user_id),
            reply_markup=create_main_menu_keyboard(user_id)
        )
        return ConversationState.MAIN_MENU
    
    elif data.startswith(CallbackData.EXERCISE_PREFIX):
        exercise = data[len(CallbackData.EXERCISE_PREFIX):]
        context.user_data['current_exercise'] = exercise
        
        await query.edit_message_text(
            get_message('select_set', user_id, exercise=exercise),
            parse_mode='Markdown',
            reply_markup=create_sets_keyboard(user_id)
        )
        return ConversationState.SET_SELECT
    
    return ConversationState.EXERCISE_SELECT

async def add_exercise_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    exercise_name = update.message.text.strip()
    
    add_exercise(exercise_name)
    await update.message.reply_text(get_message('exercise_added', user_id, name=exercise_name))
    
    category = active_workouts.get(user_id, {}).get('category')
    await update.message.reply_text(
        get_message('select_exercise', user_id),
        reply_markup=create_exercises_keyboard(category)
    )
    return ConversationState.EXERCISE_SELECT

async def exercise_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    
    logger.info(f"User {user_id} entered: {text}")
    
    if user_id not in active_workouts:
        logger.warning(f"No active workout for user {user_id}")
        await update.message.reply_text(
            get_message('no_active_workout', user_id),
            reply_markup=create_main_menu_keyboard(user_id)
        )
        return ConversationState.MAIN_MENU
    
    exercise = context.user_data.get('current_exercise')
    if not exercise:
        logger.warning(f"No current exercise for user {user_id}")
        category = active_workouts.get(user_id, {}).get('category')
        await update.message.reply_text(
            get_message('invalid_input', user_id),
            reply_markup=create_exercises_keyboard(category)
        )
        return ConversationState.EXERCISE_SELECT
    
    sets, reps, weight = None, None, None
    
    parts = text.split()
    
    if len(parts) >= 2:
        try:
            sets = int(parts[0])
            reps = parts[1]
            if len(parts) >= 3:
                weight = float(parts[2])
        except (ValueError, IndexError):
            logger.error(f"Failed to parse input: {text}")
    
    if not sets or not reps:
        logger.warning(f"Invalid input from user {user_id}: {text}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=CallbackData.BACK)]]
        await update.message.reply_text(
            "❌ Неверный формат. Введите: *подходы повторения вес*\n\nПримеры:\n• 3 12\n• 4 10 50\n• 5 5 100",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationState.EXERCISE_INPUT
    
    workout_id = active_workouts[user_id]['workout_id']
    add_exercise_to_workout(workout_id, exercise, sets, reps, weight)
    logger.info(f"Exercise {exercise} added to workout {workout_id}: {sets}x{reps}, weight={weight}")
    
    weight_str = f" ({weight} кг)" if weight else ""
    await update.message.reply_text(
        get_message('exercise_added', user_id, exercise=exercise, sets=sets, reps=reps, weight=weight_str),
        parse_mode='Markdown'
    )
    
    del context.user_data['current_exercise']
    
    category = active_workouts[user_id].get('category')
    logger.info(f"Returning to exercise selection for user {user_id}")
    await update.message.reply_text(
        get_message('select_exercise', user_id),
        reply_markup=create_exercises_keyboard(category)
    )
    return ConversationState.EXERCISE_SELECT

async def exercise_input_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == CallbackData.BACK:
        if 'current_exercise' in context.user_data:
            del context.user_data['current_exercise']
        
        category = active_workouts.get(user_id, {}).get('category')
        await query.edit_message_text(
            get_message('select_exercise', user_id),
            reply_markup=create_exercises_keyboard(category)
        )
        return ConversationState.EXERCISE_SELECT
    
    return ConversationState.EXERCISE_INPUT

async def set_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == CallbackData.BACK:
        if 'current_exercise' in context.user_data:
            del context.user_data['current_exercise']
        
        category = active_workouts.get(user_id, {}).get('category')
        await query.edit_message_text(
            get_message('select_exercise', user_id),
            reply_markup=create_exercises_keyboard(category)
        )
        return ConversationState.EXERCISE_SELECT
    
    elif data == CallbackData.ADD_SET:
        await query.edit_message_text(get_message('enter_set_name', user_id))
        return ConversationState.ADD_SET_NAME
    
    elif data == CallbackData.DELETE_SET:
        await query.edit_message_text(
            "🗑️ Выберите подход для удаления:",
            reply_markup=create_delete_sets_keyboard(user_id)
        )
        return ConversationState.SET_SELECT
    
    elif data.startswith("del_set_"):
        set_name = data[8:]
        if delete_user_set(user_id, set_name):
            await query.answer(f"✅ Подход '{set_name}' удалён")
            exercise = context.user_data.get('current_exercise', '')
            await query.edit_message_text(
                get_message('select_set', user_id, exercise=exercise),
                parse_mode='Markdown',
                reply_markup=create_sets_keyboard(user_id)
            )
        else:
            await query.answer(f"❌ Не удалось удалить '{set_name}'")
        return ConversationState.SET_SELECT
    
    elif data.startswith(CallbackData.SET_PREFIX):
        set_name = data[len(CallbackData.SET_PREFIX):]
        set_data = get_set_by_name(user_id, set_name)
        
        if set_data:
            _, _, sets, reps, weight = set_data
            exercise = context.user_data.get('current_exercise')
            
            if exercise and user_id in active_workouts:
                workout_id = active_workouts[user_id]['workout_id']
                add_exercise_to_workout(workout_id, exercise, sets, reps, weight)
                logger.info(f"Exercise {exercise} added with set {set_name}")
                
                weight_str = f" ({weight} кг)" if weight else ""
                await query.answer(f"✅ {exercise}: {sets}x{reps}{weight_str}")
                
                del context.user_data['current_exercise']
                
                category = active_workouts[user_id].get('category')
                await query.edit_message_text(
                    get_message('select_exercise', user_id),
                    reply_markup=create_exercises_keyboard(category)
                )
                return ConversationState.EXERCISE_SELECT
    
    return ConversationState.SET_SELECT

async def add_set_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    
    parts = text.lower().replace('х', 'x').split('x')
    if len(parts) >= 2:
        try:
            sets = int(parts[0])
            reps = parts[1]
            weight = float(parts[2]) if len(parts) >= 3 else None
            
            add_user_set(user_id, text, sets, reps, weight)
            await update.message.reply_text(get_message('set_added', user_id, name=text))
            
            exercise = context.user_data.get('current_exercise', '')
            await update.message.reply_text(
                get_message('select_set', user_id, exercise=exercise),
                parse_mode='Markdown',
                reply_markup=create_sets_keyboard(user_id)
            )
            return ConversationState.SET_SELECT
        except (ValueError, IndexError):
            pass
    
    await update.message.reply_text(
        "❌ Неверный формат. Введите: *подходы x повторения*\n\nПримеры:\n• 3x12\n• 4x10\n• 5x5",
        parse_mode='Markdown'
    )
    return ConversationState.ADD_SET_NAME

async def history_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == CallbackData.BACK:
        await query.edit_message_text(
            get_message('start', user_id),
            reply_markup=create_main_menu_keyboard(user_id)
        )
        return ConversationState.MAIN_MENU
    
    elif data.startswith(CallbackData.HISTORY_PAGE_PREFIX):
        page = int(data[len(CallbackData.HISTORY_PAGE_PREFIX):])
        workouts = get_user_workouts(user_id)
        await query.edit_message_text(
            get_message('history_title', user_id, total=len(workouts), exercises="", last=""),
            reply_markup=create_history_keyboard(workouts, page),
            parse_mode='Markdown'
        )
        return ConversationState.HISTORY_MENU
    
    elif data.startswith(CallbackData.HISTORY_DETAIL_PREFIX):
        workout_id = int(data[len(CallbackData.HISTORY_DETAIL_PREFIX):])
        details = get_workout_details(workout_id)
        
        if details:
            workout = details['workout']
            exercises = details['exercises']
            
            category = workout[3]
            date = datetime.fromisoformat(workout[4]).strftime("%d.%m.%Y %H:%M")
            
            exercises_text = ""
            for ex in exercises:
                ex_name, sets, reps, weight, _ = ex
                weight_str = f" ({weight} кг)" if weight else ""
                exercises_text += f"• {ex_name}: {sets}x{reps}{weight_str}\n"
            
            if not exercises_text:
                exercises_text = get_message('no_exercises', user_id)
            
            text = get_message('history_detail', user_id, date=date, category=category, exercises=exercises_text)
            
            workouts = get_user_workouts(user_id)
            keyboard = create_history_keyboard(workouts)
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        
        return ConversationState.HISTORY_MENU
    
    return ConversationState.HISTORY_MENU

async def settings_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == CallbackData.BACK:
        await query.edit_message_text(
            get_message('start', user_id),
            reply_markup=create_main_menu_keyboard(user_id)
        )
        return ConversationState.MAIN_MENU
    
    elif data.startswith(CallbackData.SETTINGS_LANGUAGE_PREFIX):
        lang = data[len(CallbackData.SETTINGS_LANGUAGE_PREFIX):]
        set_language(user_id, lang)
        settings = get_user_settings(user_id)
        
        await query.edit_message_text(
            get_message('settings_updated', user_id),
            parse_mode='Markdown'
        )
        
        lang_display = "Русский" if lang == 'ru' else "English"
        units = "Кг" if settings['units'] == 'metric' else "Фунты"
        notif = "Вкл" if settings['notifications_enabled'] else "Выкл"
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=get_message('settings_title', user_id, language=lang_display, units=units, notifications=notif),
            reply_markup=create_settings_keyboard(user_id),
            parse_mode='Markdown'
        )
        return ConversationState.SETTINGS_MENU
    
    elif data.startswith(CallbackData.SETTINGS_UNITS_PREFIX):
        units = data[len(CallbackData.SETTINGS_UNITS_PREFIX):]
        update_user_settings(user_id, units=units)
        settings = get_user_settings(user_id)
        
        lang_display = "Русский" if settings['language'] == 'ru' else "English"
        units_display = "Кг" if units == 'metric' else "Фунты"
        notif = "Вкл" if settings['notifications_enabled'] else "Выкл"
        
        await query.edit_message_text(
            get_message('settings_updated', user_id),
            parse_mode='Markdown'
        )
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=get_message('settings_title', user_id, language=lang_display, units=units_display, notifications=notif),
            reply_markup=create_settings_keyboard(user_id),
            parse_mode='Markdown'
        )
        return ConversationState.SETTINGS_MENU
    
    elif data == CallbackData.SETTINGS_NOTIFICATIONS:
        settings = get_user_settings(user_id)
        new_state = not settings['notifications_enabled']
        set_notifications(user_id, new_state)
        
        lang_display = "Русский" if settings['language'] == 'ru' else "English"
        units = "Кг" if settings['units'] == 'metric' else "Фунты"
        notif_display = "Вкл" if new_state else "Выкл"
        
        await query.edit_message_text(
            get_message('settings_updated', user_id),
            parse_mode='Markdown'
        )
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=get_message('settings_title', user_id, language=lang_display, units=units, notifications=notif_display),
            reply_markup=create_settings_keyboard(user_id),
            parse_mode='Markdown'
        )
        return ConversationState.SETTINGS_MENU
    
    return ConversationState.SETTINGS_MENU

def main():
    Thread(target=run_flask, daemon=True).start()
    
    application = Application.builder().token(TOKEN).build()
    
    main_conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ConversationState.MAIN_MENU: [
                CallbackQueryHandler(main_menu_callback),
            ],
            ConversationState.CATEGORY_SELECT: [
                CallbackQueryHandler(category_select_callback),
            ],
            ConversationState.EXERCISE_SELECT: [
                CallbackQueryHandler(exercise_select_callback),
            ],
            ConversationState.SET_SELECT: [
                CallbackQueryHandler(set_select_callback),
            ],
            ConversationState.ADD_SET_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_set_name_handler),
            ],
            ConversationState.EXERCISE_INPUT: [
                CallbackQueryHandler(exercise_input_callback),
                MessageHandler(filters.TEXT & ~filters.COMMAND, exercise_input_handler),
            ],
            ConversationState.ADD_CATEGORY_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_category_name_handler),
            ],
            ConversationState.ADD_EXERCISE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_exercise_name_handler),
            ],
            ConversationState.HISTORY_MENU: [
                CallbackQueryHandler(history_menu_callback),
            ],
            ConversationState.SETTINGS_MENU: [
                CallbackQueryHandler(settings_menu_callback),
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_handler),
            CommandHandler('start', start),
            CommandHandler('help', help_command),
        ],
        per_user=True,
        per_chat=True,
    )
    
    application.add_handler(main_conv)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("history", lambda u, c: main_menu_callback(u, c)))
    application.add_handler(CommandHandler("settings", lambda u, c: main_menu_callback(u, c)))
    
    logger.info("Bot started successfully")
    application.run_polling(allowed_updates=['message', 'callback_query'])

if __name__ == '__main__':
    main()
