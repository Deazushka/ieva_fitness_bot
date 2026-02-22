import logging
import re
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

from .constants import State, Callback, t
from .database import Database
from .keyboards import (
    main_menu_keyboard,
    categories_keyboard,
    exercises_keyboard,
    exercise_sets_keyboard,
    delete_category_keyboard,
    delete_exercise_keyboard,
    settings_keyboard,
    history_keyboard,
    back_keyboard,
)

logger = logging.getLogger(__name__)


class Handlers:
    def __init__(self, db: Database):
        self.db = db

    def register(self, application: Application) -> None:
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                State.MAIN_MENU: [
                    CallbackQueryHandler(self.start_workout, pattern=f"^{Callback.START_WORKOUT}$"),
                    CallbackQueryHandler(self.show_history, pattern=f"^{Callback.HISTORY}$"),
                    CallbackQueryHandler(self.show_settings, pattern=f"^{Callback.SETTINGS}$"),
                    CallbackQueryHandler(self.show_help, pattern=f"^{Callback.HELP}$"),
                ],
                State.CATEGORY_SELECT: [
                    CallbackQueryHandler(self.select_category, pattern=f"^{Callback.CATEGORY}_"),
                    CallbackQueryHandler(self.add_category_start, pattern=f"^{Callback.ADD_CATEGORY}$"),
                    CallbackQueryHandler(self.delete_category_menu, pattern=f"^{Callback.DELETE_CATEGORY}$"),
                    CallbackQueryHandler(self.back_to_main, pattern=f"^{Callback.BACK}$"),
                ],
                State.ADD_CATEGORY_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_category_name),
                ],
                State.DELETE_CATEGORY: [
                    CallbackQueryHandler(self.delete_category_confirm, pattern=f"^{Callback.DELETE_CATEGORY_CONFIRM}_"),
                    CallbackQueryHandler(self.back_to_categories, pattern=f"^{Callback.BACK}$"),
                ],
                State.EXERCISE_SELECT: [
                    CallbackQueryHandler(self.select_exercise, pattern=f"^{Callback.EXERCISE}_"),
                    CallbackQueryHandler(self.add_exercise_start, pattern=f"^{Callback.ADD_EXERCISE}$"),
                    CallbackQueryHandler(self.delete_exercise_menu, pattern=f"^{Callback.DELETE_EXERCISE}$"),
                    CallbackQueryHandler(self.finish_workout, pattern=f"^{Callback.FINISH_WORKOUT}$"),
                    CallbackQueryHandler(self.cancel_workout, pattern=f"^{Callback.CANCEL_WORKOUT}$"),
                    CallbackQueryHandler(self.back_to_categories, pattern=f"^{Callback.BACK}$"),
                ],
                State.ADD_EXERCISE_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_exercise_name),
                ],
                State.DELETE_EXERCISE: [
                    CallbackQueryHandler(self.delete_exercise_confirm, pattern=f"^{Callback.DELETE_EXERCISE_CONFIRM}_"),
                    CallbackQueryHandler(self.back_to_exercises, pattern=f"^{Callback.BACK}$"),
                ],
                State.EXERCISE_DETAIL: [
                    CallbackQueryHandler(self.select_exercise_set, pattern=f"^{Callback.EXERCISE_SET}_"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.custom_set),
                    CallbackQueryHandler(self.back_to_exercises, pattern=f"^{Callback.BACK}$"),
                ],
                State.HISTORY_MENU: [
                    CallbackQueryHandler(self.show_workout_detail, pattern=f"^{Callback.WORKOUT}_"),
                    CallbackQueryHandler(self.history_page, pattern=f"^{Callback.HISTORY_PAGE}_"),
                    CallbackQueryHandler(self.back_to_main, pattern=f"^{Callback.MAIN_MENU}$"),
                ],
                State.SETTINGS_MENU: [
                    CallbackQueryHandler(self.set_language, pattern=f"^set_lang_"),
                    CallbackQueryHandler(self.set_units, pattern=f"^set_units_"),
                    CallbackQueryHandler(self.set_notifications, pattern=f"^{Callback.SET_NOTIF}$"),
                    CallbackQueryHandler(self.back_to_main, pattern=f"^{Callback.BACK}$"),
                ],
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel),
                CommandHandler("start", self.start),
            ],
            per_message=False,
            per_chat=True,
        )

        application.add_handler(conv_handler)

    async def get_lang(self, user_id: int) -> str:
        settings = await self.db.get_user_settings(user_id)
        return settings.get("language", "ru")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = await self.db.get_or_create_user(user.id, user.username)
        context.user_data["user_id"] = user_id

        lang = await self.get_lang(user_id)
        context.user_data["lang"] = lang

        keyboard = main_menu_keyboard(lang)
        if update.message:
            await update.message.reply_text(t("welcome", lang), reply_markup=keyboard)
        else:
            await update.callback_query.edit_message_text(t("welcome", lang), reply_markup=keyboard)

        return State.MAIN_MENU

    async def back_to_main(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        keyboard = main_menu_keyboard(lang)
        await update.callback_query.edit_message_text(t("welcome", lang), reply_markup=keyboard)
        return State.MAIN_MENU

    async def start_workout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        categories = await self.db.get_categories()
        keyboard = categories_keyboard(categories, lang)
        await update.callback_query.edit_message_text(t("select_category", lang), reply_markup=keyboard)
        return State.CATEGORY_SELECT

    async def select_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        callback_data = update.callback_query.data
        logger.info(f"select_category called with callback_data: {callback_data}")
        
        category_id = int(callback_data.split("_")[1])
        logger.info(f"category_id: {category_id}")

        categories = await self.db.get_categories()
        category = next((c for c in categories if c["id"] == category_id), None)
        if not category:
            logger.warning(f"Category not found for id: {category_id}")
            return State.CATEGORY_SELECT

        category_name = category["name_ru"] if lang == "ru" else category["name_en"]
        context.user_data["category_id"] = category_id
        context.user_data["category_name"] = category_name
        logger.info(f"Selected category: {category_name}")

        user_id = context.user_data.get("user_id")
        await self.db.start_workout(user_id, category_name)

        exercises = await self.db.get_exercises(category_id)
        logger.info(f"Found {len(exercises)} exercises for category {category_id}")
        
        keyboard = exercises_keyboard(exercises, category_id, lang)
        await update.callback_query.edit_message_text(
            t("select_exercise", lang, category=category_name),
            reply_markup=keyboard
        )
        return State.EXERCISE_SELECT

    async def back_to_categories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        categories = await self.db.get_categories()
        keyboard = categories_keyboard(categories, lang)
        await update.callback_query.edit_message_text(t("select_category", lang), reply_markup=keyboard)
        return State.CATEGORY_SELECT

    async def select_exercise(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        callback_data = update.callback_query.data
        logger.info(f"select_exercise called with callback_data: {callback_data}")
        
        exercise_id = int(callback_data.split("_")[1])
        logger.info(f"exercise_id: {exercise_id}")

        exercises = await self.db.get_exercises()
        exercise = next((e for e in exercises if e["id"] == exercise_id), None)
        if not exercise:
            logger.warning(f"Exercise not found for id: {exercise_id}")
            return State.EXERCISE_SELECT

        exercise_name = exercise["name_ru"] if lang == "ru" else exercise["name_en"]
        context.user_data["exercise_id"] = exercise_id
        context.user_data["exercise_name"] = exercise_name

        keyboard = exercise_sets_keyboard(exercise_id, lang)
        await update.callback_query.edit_message_text(
            t("select_set", lang, exercise=exercise_name),
            reply_markup=keyboard
        )
        return State.EXERCISE_DETAIL

    async def back_to_exercises(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        category_id = context.user_data.get("category_id")
        category_name = context.user_data.get("category_name", "")

        exercises = await self.db.get_exercises(category_id)
        keyboard = exercises_keyboard(exercises, category_id, lang)
        await update.callback_query.edit_message_text(
            t("select_exercise", lang, category=category_name),
            reply_markup=keyboard
        )
        return State.EXERCISE_SELECT

    async def select_exercise_set(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        callback_data = update.callback_query.data
        parts = callback_data.split("_")
        exercise_id = int(parts[2])
        set_preset = parts[3]

        sets, reps = map(int, set_preset.split("x"))
        await self._add_exercise_to_workout(context, sets, reps)

        exercise_name = context.user_data.get("exercise_name", "")
        await update.callback_query.answer(t("workout_added", lang, exercise=exercise_name, sets=sets, reps=reps))

        return await self.back_to_exercises(update, context)

    async def custom_set(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        text = update.message.text.strip()

        match = re.match(r"(\d+)\s+(\d+)(?:\s+(\d+(?:\.\d+)?))?", text)
        if not match:
            await update.message.reply_text(t("select_set", lang, exercise=context.user_data.get("exercise_name", "")))
            return State.EXERCISE_DETAIL

        sets = int(match.group(1))
        reps = int(match.group(2))
        weight = float(match.group(3)) if match.group(3) else None

        await self._add_exercise_to_workout(context, sets, reps, weight)

        exercise_name = context.user_data.get("exercise_name", "")
        category_id = context.user_data.get("category_id")

        exercises = await self.db.get_exercises(category_id)
        keyboard = exercises_keyboard(exercises, category_id, lang)
        await update.message.reply_text(
            t("workout_added", lang, exercise=exercise_name, sets=sets, reps=reps),
            reply_markup=keyboard
        )
        return State.EXERCISE_SELECT

    async def _add_exercise_to_workout(self, context: ContextTypes.DEFAULT_TYPE, sets: int, reps: int, weight: float = None):
        user_id = context.user_data.get("user_id")
        exercise_name = context.user_data.get("exercise_name", "")

        workout = await self.db.get_active_workout(user_id)
        if workout:
            await self.db.add_workout_exercise(workout["id"], exercise_name, sets, reps, weight)

    async def finish_workout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        user_id = context.user_data.get("user_id")

        workout = await self.db.get_active_workout(user_id)
        if workout:
            await self.db.finish_workout(workout["id"])
            exercises = await self.db.get_workout_exercises(workout["id"])
            count = len(exercises)
        else:
            count = 0

        keyboard = main_menu_keyboard(lang)
        await update.callback_query.edit_message_text(
            t("workout_finished", lang, count=count),
            reply_markup=keyboard
        )
        return State.MAIN_MENU

    async def cancel_workout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        user_id = context.user_data.get("user_id")

        workout = await self.db.get_active_workout(user_id)
        if workout:
            await self.db.cancel_workout(workout["id"])

        keyboard = main_menu_keyboard(lang)
        await update.callback_query.edit_message_text(t("workout_cancelled", lang), reply_markup=keyboard)
        return State.MAIN_MENU

    async def add_category_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        keyboard = back_keyboard(lang)
        await update.callback_query.edit_message_text(t("enter_category_name", lang), reply_markup=keyboard)
        return State.ADD_CATEGORY_NAME

    async def add_category_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        name = update.message.text.strip()

        success = await self.db.add_category(name)
        if success:
            await update.message.reply_text(t("category_added", lang, name=name))
        else:
            await update.message.reply_text("Category already exists!")

        categories = await self.db.get_categories()
        keyboard = categories_keyboard(categories, lang)
        await update.message.reply_text(t("select_category", lang), reply_markup=keyboard)
        return State.CATEGORY_SELECT

    async def delete_category_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        categories = await self.db.get_categories()
        keyboard = delete_category_keyboard(categories, lang)
        await update.callback_query.edit_message_text(t("select_category_delete", lang), reply_markup=keyboard)
        return State.DELETE_CATEGORY

    async def delete_category_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        callback_data = update.callback_query.data
        category_id = int(callback_data.split("_")[2])

        categories = await self.db.get_categories()
        category = next((c for c in categories if c["id"] == category_id), None)
        name = category["name_ru"] if category else ""

        await self.db.delete_category(name)
        await update.callback_query.answer(t("category_deleted", lang, name=name))

        categories = await self.db.get_categories()
        keyboard = categories_keyboard(categories, lang)
        await update.callback_query.edit_message_text(t("select_category", lang), reply_markup=keyboard)
        return State.CATEGORY_SELECT

    async def add_exercise_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        keyboard = back_keyboard(lang)
        await update.callback_query.edit_message_text(t("enter_exercise_name", lang), reply_markup=keyboard)
        return State.ADD_EXERCISE_NAME

    async def add_exercise_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        name = update.message.text.strip()
        category_id = context.user_data.get("category_id")

        success = await self.db.add_exercise(name, category_id)
        if success:
            await update.message.reply_text(t("exercise_added", lang, name=name))
        else:
            await update.message.reply_text("Exercise already exists!")

        exercises = await self.db.get_exercises(category_id)
        keyboard = exercises_keyboard(exercises, category_id, lang)
        await update.message.reply_text(t("select_exercise", lang, category=context.user_data.get("category_name", "")), reply_markup=keyboard)
        return State.EXERCISE_SELECT

    async def delete_exercise_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        category_id = context.user_data.get("category_id")
        exercises = await self.db.get_exercises(category_id)
        keyboard = delete_exercise_keyboard(exercises, lang)
        await update.callback_query.edit_message_text(t("select_exercise_delete", lang), reply_markup=keyboard)
        return State.DELETE_EXERCISE

    async def delete_exercise_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        callback_data = update.callback_query.data
        exercise_id = int(callback_data.split("_")[2])

        exercises = await self.db.get_exercises()
        exercise = next((e for e in exercises if e["id"] == exercise_id), None)
        name = exercise["name_ru"] if exercise else ""

        await self.db.delete_exercise(name)
        await update.callback_query.answer(t("exercise_deleted", lang, name=name))

        category_id = context.user_data.get("category_id")
        exercises = await self.db.get_exercises(category_id)
        keyboard = exercises_keyboard(exercises, category_id, lang)
        await update.callback_query.edit_message_text(
            t("select_exercise", lang, category=context.user_data.get("category_name", "")),
            reply_markup=keyboard
        )
        return State.EXERCISE_SELECT

    async def show_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        user_id = context.user_data.get("user_id")

        workouts = await self.db.get_user_workouts(user_id, limit=10, offset=0)
        stats = await self.db.get_workout_stats(user_id)

        if not workouts:
            keyboard = main_menu_keyboard(lang)
            await update.callback_query.edit_message_text(t("no_workouts", lang), reply_markup=keyboard)
            return State.MAIN_MENU

        keyboard = history_keyboard(workouts, 0, lang)
        await update.callback_query.edit_message_text(
            t("history", lang, total=stats["total_workouts"], exercises=stats["total_exercises"]),
            reply_markup=keyboard
        )
        context.user_data["history_page"] = 0
        return State.HISTORY_MENU

    async def history_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        user_id = context.user_data.get("user_id")

        callback_data = update.callback_query.data
        page = int(callback_data.split("_")[1])
        context.user_data["history_page"] = page

        workouts = await self.db.get_user_workouts(user_id, limit=10, offset=page * 10)
        stats = await self.db.get_workout_stats(user_id)

        keyboard = history_keyboard(workouts, page, lang)
        await update.callback_query.edit_message_text(
            t("history", lang, total=stats["total_workouts"], exercises=stats["total_exercises"]),
            reply_markup=keyboard
        )
        return State.HISTORY_MENU

    async def show_workout_detail(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        callback_data = update.callback_query.data
        workout_id = int(callback_data.split("_")[1])

        workout = await self.db.get_workout_by_id(workout_id)
        if not workout:
            return State.HISTORY_MENU

        exercises = await self.db.get_workout_exercises(workout_id)
        page = context.user_data.get("history_page", 0)

        lines = [f"📋 Тренировка {workout['started_at'].strftime('%d.%m.%Y')}"]
        lines.append(f"Категория: {workout.get('category_name', t('free_workout', lang))}")
        lines.append("")
        for ex in exercises:
            line = f"• {ex['exercise_name']}: {ex['sets']}x{ex['reps']}"
            if ex.get("weight"):
                line += f" ({ex['weight']} кг)"
            lines.append(line)

        keyboard = history_keyboard([], page, lang)
        await update.callback_query.edit_message_text("\n".join(lines), reply_markup=keyboard)
        return State.HISTORY_MENU

    async def show_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        user_id = context.user_data.get("user_id")

        settings = await self.db.get_user_settings(user_id)
        context.user_data["settings"] = settings

        lang_name = "Русский" if settings.get("language") == "ru" else "English"
        units_name = "Кг" if settings.get("units") == "metric" else "Фунты"
        notif_name = "Вкл" if settings.get("notifications_enabled") else "Выкл"

        keyboard = settings_keyboard(settings, lang)
        await update.callback_query.edit_message_text(
            t("settings", lang, lang=lang_name, units=units_name, notif=notif_name),
            reply_markup=keyboard
        )
        return State.SETTINGS_MENU

    async def set_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang_code = "ru" if "ru" in update.callback_query.data else "en"
        user_id = context.user_data.get("user_id")

        await self.db.update_user_settings(user_id, language=lang_code)
        context.user_data["lang"] = lang_code

        settings = await self.db.get_user_settings(user_id)
        lang_name = "Русский" if lang_code == "ru" else "English"
        units_name = "Кг" if settings.get("units") == "metric" else "Фунты"
        notif_name = "Вкл" if settings.get("notifications_enabled") else "Выкл"

        keyboard = settings_keyboard(settings, lang_code)
        await update.callback_query.edit_message_text(
            t("settings", lang_code, lang=lang_name, units=units_name, notif=notif_name),
            reply_markup=keyboard
        )
        return State.SETTINGS_MENU

    async def set_units(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        user_id = context.user_data.get("user_id")
        units = "metric" if "metric" in update.callback_query.data else "imperial"

        await self.db.update_user_settings(user_id, units=units)

        settings = await self.db.get_user_settings(user_id)
        lang_name = "Русский" if settings.get("language") == "ru" else "English"
        units_name = "Кг" if settings.get("units") == "metric" else "Фунты"
        notif_name = "Вкл" if settings.get("notifications_enabled") else "Выкл"

        keyboard = settings_keyboard(settings, lang)
        await update.callback_query.edit_message_text(
            t("settings", lang, lang=lang_name, units=units_name, notif=notif_name),
            reply_markup=keyboard
        )
        return State.SETTINGS_MENU

    async def set_notifications(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        user_id = context.user_data.get("user_id")
        settings = context.user_data.get("settings", {})

        new_value = not settings.get("notifications_enabled", False)
        await self.db.update_user_settings(user_id, notifications_enabled=new_value)
        settings["notifications_enabled"] = new_value
        context.user_data["settings"] = settings

        lang_name = "Русский" if settings.get("language") == "ru" else "English"
        units_name = "Кг" if settings.get("units") == "metric" else "Фунты"
        notif_name = "Вкл" if new_value else "Выкл"

        keyboard = settings_keyboard(settings, lang)
        await update.callback_query.edit_message_text(
            t("settings", lang, lang=lang_name, units=units_name, notif=notif_name),
            reply_markup=keyboard
        )
        return State.SETTINGS_MENU

    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        help_text = t("welcome", lang) + "\n\n"
        help_text += "🏋️ /start - Главное меню\n"
        help_text += "📊 История - Просмотр тренировок\n"
        help_text += "⚙️ Настройки - Язык, единицы\n"
        help_text += "❓ Помощь - Эта справка\n"

        keyboard = main_menu_keyboard(lang)
        await update.callback_query.edit_message_text(help_text, reply_markup=keyboard)
        return State.MAIN_MENU

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get("lang", "ru")
        keyboard = main_menu_keyboard(lang)
        await update.message.reply_text(t("welcome", lang), reply_markup=keyboard)
        return State.MAIN_MENU
