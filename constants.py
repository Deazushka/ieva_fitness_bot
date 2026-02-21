from enum import IntEnum

class ConversationState(IntEnum):
    MAIN_MENU = 0
    WORKOUT_ACTIVE = 1
    CATEGORY_SELECT = 2
    EXERCISE_SELECT = 3
    EXERCISE_INPUT = 4
    
    ADD_CATEGORY = 10
    ADD_CATEGORY_NAME = 11
    DELETE_CATEGORY = 12
    
    ADD_EXERCISE = 13
    ADD_EXERCISE_NAME = 14
    DELETE_EXERCISE = 15
    
    SETTINGS_MENU = 20
    SETTINGS_LANGUAGE = 21
    SETTINGS_UNITS = 22
    SETTINGS_NOTIFICATIONS = 23
    
    HISTORY_MENU = 30
    HISTORY_VIEW = 31
    
    END = -1


class CallbackData:
    START_WORKOUT = "start_workout"
    HISTORY = "history"
    SETTINGS = "settings"
    HELP = "help"
    
    CATEGORY_PREFIX = "cat_"
    ADD_CATEGORY = "add_category"
    DELETE_CATEGORY = "delete_category"
    
    EXERCISE_PREFIX = "ex_"
    ADD_EXERCISE = "add_exercise"
    DELETE_EXERCISE = "delete_exercise"
    FINISH_WORKOUT = "finish_workout"
    CANCEL_WORKOUT = "cancel_workout"
    
    HISTORY_PAGE_PREFIX = "hist_page_"
    HISTORY_DETAIL_PREFIX = "hist_det_"
    
    SETTINGS_LANGUAGE_PREFIX = "set_lang_"
    SETTINGS_UNITS_PREFIX = "set_units_"
    SETTINGS_NOTIFICATIONS = "set_notif"
    
    BACK = "back"
    CANCEL = "cancel"
    CONFIRM = "confirm"
    MAIN_MENU = "main_menu"


MESSAGES = {
    'ru': {
        'start': "🏋️ Добро пожаловать в Fitness Tracker Bot!\n\nВыберите действие:",
        'help': "📖 *Справка по использованию:*\n\n" \
                "• /start - Главное меню\n" \
                "• /history - История тренировок\n" \
                "• /settings - Настройки\n" \
                "• /cancel - Отмена\n\n" \
                "*Как начать тренировку:*\n" \
                "1. Нажмите '🏋️ Начать тренировку'\n" \
                "2. Выберите категорию\n" \
                "3. Выберите упражнение\n" \
                "4. Введите подходы и повторения\n\n" \
                "*Формат ввода:*\n" \
                "• 3x12 - 3 подхода по 12 повторений\n" \
                "• 4x10,50 - 4x10 с весом 50 кг\n" \
                "• 5x5x100 - 5x5 с весом 100 кг",
        'workout_started': "✅ Тренировка начата! Категория: *{category}*",
        'select_category': "📋 Выберите категорию тренировки:",
        'select_exercise': "💪 Выберите упражнение:",
        'enter_sets_reps': "🔢 Введите количество подходов и повторений.\n\n" \
                          "*Примеры:*\n" \
                          "• 3x12\n" \
                          "• 4x10,50\n" \
                          "• 5x5x100",
        'exercise_added': "✅ Упражнение добавлено: *{exercise}*\n" \
                         "Подходы: {sets}x{reps}" + (" ({weight} кг)" if weight else ""),
        'invalid_input': "❌ Неверный формат ввода. Попробуйте снова.\n\n" \
                        "*Примеры:*\n• 3x12\n• 4x10,50",
        'workout_finished': "🎉 *Тренировка завершена!*\n\n" \
                           "_Категория:_ {category}\n" \
                           "_Упражнений:_ {total}\n\n" \
                           "{exercises}\n\n" \
                           "_Дата:_ {date}",
        'no_active_workout': "❌ Нет активной тренировки",
        'history_title': "📊 *История тренировок*\n\nВсего тренировок: {total}\nУпражнений: {exercises}\n\nПоследняя: {last}",
        'history_empty': "📭 История тренировок пуста",
        'history_entry': "• {date} - {category} ({exercises} упр.)",
        'history_detail': "📋 *Тренировка {date}*\n" \
                         "_Категория:_ {category}\n\n" \
                         "{exercises}",
        'no_exercises': "Нет упражнений",
        'settings_title': "⚙️ *Настройки*\n\n" \
                          "• Язык: {language}\n" \
                          "• Единицы: {units}\n" \
                          "• Уведомления: {notifications}",
        'settings_updated': "✅ Настройки обновлены",
        'category_added': "✅ Категория '{name}' добавлена",
        'category_deleted': "✅ Категория '{name}' удалена",
        'exercise_added': "✅ Упражнение '{name}' добавлено",
        'exercise_deleted': "✅ Упражнение '{name}' удалено",
        'enter_category_name': "Введите название новой категории:",
        'enter_exercise_name': "Введите название нового упражнения:",
        'cancel_workout': "❌ Тренировка отменена",
        'workout_cancelled': "✅ Тренировка отменена",
        'back_to_main': "Возврат в главное меню...",
        'language_ru': "Русский 🇷🇺",
        'language_en': "English 🇬🇧",
        'units_metric': "Метрические (кг) ⚖️",
        'units_imperial': "Имперские (фунты) ⚖️",
        'notifications_on': "Включены 🔔",
        'notifications_off': "Выключены 🔕",
        'current_language': "Русский" if 'ru' else "English",
        'current_units': "Метрические (кг)" if 'metric' else "Имперские (фунты)",
    },
    'en': {
        'start': "🏋️ Welcome to Fitness Tracker Bot!\n\nChoose an action:",
        'help': "📖 *Help:*\n\n" \
                "• /start - Main menu\n" \
                "• /history - Workout history\n" \
                "• /settings - Settings\n" \
                "• /cancel - Cancel\n\n" \
                "*How to start workout:*\n" \
                "1. Press '🏋️ Start workout'\n" \
                "2. Choose category\n" \
                "3. Choose exercise\n" \
                "4. Enter sets and reps\n\n" \
                "*Input format:*\n" \
                "• 3x12 - 3 sets of 12 reps\n" \
                "• 4x10,50 - 4x10 with 50kg",
        'workout_started': "✅ Workout started! Category: *{category}*",
        'select_category': "📋 Select workout category:",
        'select_exercise': "💪 Select exercise:",
        'enter_sets_reps': "🔢 Enter sets and reps.\n\n" \
                          "*Examples:*\n" \
                          "• 3x12\n" \
                          "• 4x10,50\n" \
                          "• 5x5x100",
        'exercise_added': "✅ Exercise added: *{exercise}*\n" \
                           "Sets: {sets}x{reps}" + (" ({weight} kg)" if weight else ""),
        'invalid_input': "❌ Invalid format. Try again.\n\n" \
                        "*Examples:*\n• 3x12\n• 4x10,50",
        'workout_finished': "🎉 *Workout Completed!*\n\n" \
                           "_Category:_ {category}\n" \
                           "_Exercises:_ {total}\n\n" \
                           "{exercises}\n\n" \
                           "_Date:_ {date}",
        'no_active_workout': "❌ No active workout",
        'history_title': "📊 *Workout History*\n\nTotal workouts: {total}\nExercises: {exercises}\n\nLast: {last}",
        'history_empty': "📭 Workout history is empty",
        'history_entry': "• {date} - {category} ({exercises} exercises)",
        'history_detail': "📋 *Workout {date}*\n" \
                         "_Category:_ {category}\n\n" \
                         "{exercises}",
        'no_exercises': "No exercises",
        'settings_title': "⚙️ *Settings*\n\n" \
                          "• Language: {language}\n" \
                          "• Units: {units}\n" \
                          "• Notifications: {notifications}",
        'settings_updated': "✅ Settings updated",
        'category_added': "✅ Category '{name}' added",
        'category_deleted': "✅ Category '{name}' deleted",
        'exercise_added': "✅ Exercise '{name}' added",
        'exercise_deleted': "✅ Exercise '{name}' deleted",
        'enter_category_name': "Enter new category name:",
        'enter_exercise_name': "Enter new exercise name:",
        'cancel_workout': "❌ Workout cancelled",
        'workout_cancelled': "✅ Workout cancelled",
        'back_to_main': "Returning to main menu...",
        'language_ru': "Русский 🇷🇺",
        'language_en': "English 🇬🇧",
        'units_metric': "Metric (kg) ⚖️",
        'units_imperial': "Imperial (lbs) ⚖️",
        'notifications_on': "Enabled 🔔",
        'notifications_off': "Disabled 🔕",
        'current_language': "English",
        'current_units': "Metric (kg)" if 'metric' else "Imperial (lbs)",
    }
}
