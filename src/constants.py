from enum import Enum


class State(Enum):
    MAIN_MENU = 1
    CATEGORY_SELECT = 2
    EXERCISE_SELECT = 3
    EXERCISE_DETAIL = 4
    ADD_CATEGORY_NAME = 5
    DELETE_CATEGORY = 6
    ADD_EXERCISE_NAME = 7
    DELETE_EXERCISE = 8
    HISTORY_MENU = 9
    WORKOUT_DETAIL = 10
    SETTINGS_MENU = 11
    END = -1


class Callback:
    START_WORKOUT = "start_workout"
    HISTORY = "history"
    SETTINGS = "settings"
    HELP = "help"
    BACK = "back"
    MAIN_MENU = "main_menu"
    
    CATEGORY = "cat"
    ADD_CATEGORY = "add_category"
    DELETE_CATEGORY = "delete_category"
    DELETE_CATEGORY_CONFIRM = "del_cat"
    
    EXERCISE = "ex"
    ADD_EXERCISE = "add_exercise"
    DELETE_EXERCISE = "delete_exercise"
    DELETE_EXERCISE_CONFIRM = "del_ex"
    
    EXERCISE_SET = "ex_set"
    
    FINISH_WORKOUT = "finish_workout"
    CANCEL_WORKOUT = "cancel_workout"
    
    WORKOUT = "workout"
    HISTORY_PAGE = "hist_page"
    
    SET_LANG_RU = "set_lang_ru"
    SET_LANG_EN = "set_lang_en"
    SET_UNITS_METRIC = "set_units_metric"
    SET_UNITS_IMPERIAL = "set_units_imperial"
    SET_NOTIF = "set_notif"


MESSAGES = {
    "ru": {
        "welcome": "🏋️ Добро пожаловать!\nВыберите действие:",
        "select_category": "📋 Выберите категорию тренировки:",
        "select_exercise": "💪 Выберите упражнение:\nКатегория: {category}",
        "select_set": "💪 {exercise}\nВыберите подход:\n\nИли введите: <подходы> <повторы> [вес]\nПримеры: 3 12, 4 10 50",
        "settings": "⚙️ Настройки\n• Язык: {lang}\n• Единицы: {units}\n• Уведомления: {notif}",
        "history": "📊 История тренировок\nВсего: {total} | Упражнений: {exercises}",
        "no_workouts": "Тренировок пока нет. Начните с /start!",
        "workout_added": "✅ Добавлено: {exercise} - {sets}x{reps}",
        "workout_finished": "🎉 Тренировка завершена!\nУпражнений: {count}",
        "workout_cancelled": "❌ Тренировка отменена",
        "category_added": "✅ Категория добавлена: {name}",
        "category_deleted": "🗑️ Категория удалена: {name}",
        "exercise_added": "✅ Упражнение добавлено: {name}",
        "exercise_deleted": "🗑️ Упражнение удалено: {name}",
        "enter_category_name": "Введите название категории:",
        "enter_exercise_name": "Введите название упражнения:",
        "select_category_delete": "Выберите категорию для удаления:",
        "select_exercise_delete": "Выберите упражнение для удаления:",
        "back": "🔙 Назад",
        "main_menu": "🏠 Главное меню",
        "start_workout": "🏋️ Начать тренировку",
        "history_btn": "📊 История",
        "settings_btn": "⚙️ Настройки",
        "help_btn": "❓ Помощь",
        "add": "➕ Добавить",
        "delete": "🗑️ Удалить",
        "finish": "✅ Завершить",
        "cancel": "❌ Отмена",
        "lang_ru": "🇷🇺 Русский",
        "lang_en": "🇬🇧 English",
        "units_kg": "⚖️ Кг",
        "units_lb": "⚖️ Фунты",
        "notif_on": "🔔 Вкл",
        "notif_off": "🔕 Выкл",
        "free_workout": "📋 Свободная тренировка",
        "prev": "◀ Назад",
        "next": "Вперёд ▶",
    },
    "en": {
        "welcome": "🏋️ Welcome!\nSelect an action:",
        "select_category": "📋 Select workout category:",
        "select_exercise": "💪 Select exercise:\nCategory: {category}",
        "select_set": "💪 {exercise}\nSelect set:\n\nOr enter: <sets> <reps> [weight]\nExamples: 3 12, 4 10 50",
        "settings": "⚙️ Settings\n• Language: {lang}\n• Units: {units}\n• Notifications: {notif}",
        "history": "📊 Workout History\nTotal: {total} | Exercises: {exercises}",
        "no_workouts": "No workouts yet. Start with /start!",
        "workout_added": "✅ Added: {exercise} - {sets}x{reps}",
        "workout_finished": "🎉 Workout finished!\nExercises: {count}",
        "workout_cancelled": "❌ Workout cancelled",
        "category_added": "✅ Category added: {name}",
        "category_deleted": "🗑️ Category deleted: {name}",
        "exercise_added": "✅ Exercise added: {name}",
        "exercise_deleted": "🗑️ Exercise deleted: {name}",
        "enter_category_name": "Enter category name:",
        "enter_exercise_name": "Enter exercise name:",
        "select_category_delete": "Select category to delete:",
        "select_exercise_delete": "Select exercise to delete:",
        "back": "🔙 Back",
        "main_menu": "🏠 Main Menu",
        "start_workout": "🏋️ Start Workout",
        "history_btn": "📊 History",
        "settings_btn": "⚙️ Settings",
        "help_btn": "❓ Help",
        "add": "➕ Add",
        "delete": "🗑️ Delete",
        "finish": "✅ Finish",
        "cancel": "❌ Cancel",
        "lang_ru": "🇷🇺 Русский",
        "lang_en": "🇬🇧 English",
        "units_kg": "⚖️ Kg",
        "units_lb": "⚖️ Lbs",
        "notif_on": "🔔 On",
        "notif_off": "🔕 Off",
        "free_workout": "📋 Free Workout",
        "prev": "◀ Back",
        "next": "Next ▶",
    }
}


def t(key: str, language: str = "ru", **kwargs) -> str:
    msg = MESSAGES.get(language, MESSAGES["ru"]).get(key, key)
    return msg.format(**kwargs) if kwargs else msg


DEFAULT_CATEGORIES = [
    ("День ног", "Leg Day"),
    ("День рук", "Arm Day"),
    ("День спины", "Back Day"),
    ("День груди", "Chest Day"),
    ("Свободная тренировка", "Free Workout"),
]

DEFAULT_EXERCISES = {
    "День ног": [("Приседания", "Squats"), ("Жим ногами", "Leg Press"), ("Становая тяга", "Deadlift")],
    "День рук": [("Бицепс", "Biceps Curls"), ("Трицепс", "Triceps"), ("Молотки", "Hammer Curls")],
    "День спины": [("Подтягивания", "Pull-ups"), ("Тяга блока", "Lat Pulldown"), ("Тяга штанги", "Barbell Row")],
    "День груди": [("Жим лёжа", "Bench Press"), ("Разводка", "Dumbbell Fly"), ("Отжимания", "Push-ups")],
    "Свободная тренировка": [],
}

DEFAULT_SETS = ["3x12", "5x5", "4x10", "3x15", "4x8"]
