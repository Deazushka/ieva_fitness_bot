from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    keyboard = [
        ["🏋️ Начать тренировку", "📊 История"],
        ["⚙️ Настройки", "❓ Помощь"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_categories_keyboard(categories):
    # categories: список [(id, user_id, name), ...]
    keyboard = []
    row = []
    for cat in categories:
        row.append(cat['name'])
        if len(row) == 2:
             keyboard.append(row)
             row = []
    if row:
        keyboard.append(row)
        
    keyboard.append(["➕ Добавить категорию", "🗑️ Удалить категорию"])
    keyboard.append(["🔙 Назад"])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_exercises_inline_keyboard(exercises, page=1, per_page=10, prefix="ex_sel"):
    # exercises: список
    start = (page - 1) * per_page
    end = start + per_page
    current_items = exercises[start:end]
    total_pages = (len(exercises) + per_page - 1) // per_page
    
    keyboard = []
    row = []
    for ex in current_items:
        row.append(InlineKeyboardButton(ex['name'], callback_data=f"{prefix}_{ex['id']}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    # Пагинация
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"{prefix}_page_{page-1}"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"{prefix}_page_{page+1}"))
        
    if nav_row:
        keyboard.append(nav_row)
        
    return InlineKeyboardMarkup(keyboard)

def get_exercise_management_reply_keyboard():
    keyboard = [
        ["➕ Добавить упражнение", "🗑️ Удалить упражнение"],
        ["✅ Завершить тренировку", "❌ Отменить тренировку"],
        ["🔙 Назад (к категориям)"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_presets_keyboard(presets):
    # presets: [(reps, weight), ...]
    keyboard = []
    row = []
    for p in presets:
        w_str = f" x {p['weight']}" if p['weight'] else ""
        text = f"{p['reps']}{w_str}"
        row.append(text)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    keyboard.append(["🔙 Назад (к упражнениям)"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_history_inline_keyboard(workouts, page=1, per_page=5):
    # workouts: [(id, started_at, category_name), ...]
    start = (page - 1) * per_page
    end = start + per_page
    current_items = workouts[start:end]
    total_pages = (len(workouts) + per_page - 1) // per_page
    
    keyboard = []
    for w in current_items:
        # Format date
        # w['started_at'] is string if coming from sqlite directly
        try:
             dt_str = w['started_at'][:10]
        except:
             dt_str = "Unknown"
        keyboard.append([InlineKeyboardButton(f"{dt_str} - {w['category_name']}", callback_data=f"hist_{w['id']}")])
        
    # Пагинация
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"hist_page_{page-1}"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"hist_page_{page+1}"))
        
    if nav_row:
        keyboard.append(nav_row)
        
    return InlineKeyboardMarkup(keyboard)

def get_history_reply_keyboard():
     return ReplyKeyboardMarkup([["🔙 Назад"]], resize_keyboard=True)
