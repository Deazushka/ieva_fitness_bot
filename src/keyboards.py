from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .constants import Callback, t, DEFAULT_SETS


def main_menu_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(t("start_workout", lang), callback_data=Callback.START_WORKOUT)],
        [
            InlineKeyboardButton(t("history_btn", lang), callback_data=Callback.HISTORY),
            InlineKeyboardButton(t("settings_btn", lang), callback_data=Callback.SETTINGS),
        ],
        [InlineKeyboardButton(t("help_btn", lang), callback_data=Callback.HELP)],
    ]
    return InlineKeyboardMarkup(buttons)


def categories_keyboard(categories: list, lang: str = "ru") -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for cat in categories:
        name = cat["name_ru"] if lang == "ru" else cat["name_en"]
        btn = InlineKeyboardButton(f"• {name}", callback_data=f"{Callback.CATEGORY}_{cat['id']}")
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(t("add", lang), callback_data=Callback.ADD_CATEGORY),
        InlineKeyboardButton(t("delete", lang), callback_data=Callback.DELETE_CATEGORY),
    ])
    buttons.append([InlineKeyboardButton(t("back", lang), callback_data=Callback.BACK)])

    return InlineKeyboardMarkup(buttons)


def exercises_keyboard(exercises: list, category_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for ex in exercises:
        name = ex["name_ru"] if lang == "ru" else ex["name_en"]
        btn = InlineKeyboardButton(f"• {name}", callback_data=f"{Callback.EXERCISE}_{ex['id']}")
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(t("add", lang), callback_data=Callback.ADD_EXERCISE),
        InlineKeyboardButton(t("delete", lang), callback_data=Callback.DELETE_EXERCISE),
    ])
    buttons.append([
        InlineKeyboardButton(t("finish", lang), callback_data=Callback.FINISH_WORKOUT),
        InlineKeyboardButton(t("cancel", lang), callback_data=Callback.CANCEL_WORKOUT),
    ])
    buttons.append([InlineKeyboardButton(t("back", lang), callback_data=Callback.BACK)])

    return InlineKeyboardMarkup(buttons)


def exercise_sets_keyboard(exercise_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for preset in DEFAULT_SETS:
        btn = InlineKeyboardButton(f"📊 {preset}", callback_data=f"{Callback.EXERCISE_SET}_{exercise_id}_{preset}")
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(t("add", lang), callback_data=f"custom_set_{exercise_id}"),
        InlineKeyboardButton(t("delete", lang), callback_data=Callback.DELETE_EXERCISE),
    ])
    buttons.append([InlineKeyboardButton(t("back", lang), callback_data=Callback.BACK)])

    return InlineKeyboardMarkup(buttons)


def delete_category_keyboard(categories: list, lang: str = "ru") -> InlineKeyboardMarkup:
    buttons = []
    for cat in categories:
        name = cat["name_ru"] if lang == "ru" else cat["name_en"]
        btn = InlineKeyboardButton(f"🗑️ {name}", callback_data=f"{Callback.DELETE_CATEGORY_CONFIRM}_{cat['id']}")
        buttons.append([btn])
    buttons.append([InlineKeyboardButton(t("back", lang), callback_data=Callback.BACK)])
    return InlineKeyboardMarkup(buttons)


def delete_exercise_keyboard(exercises: list, lang: str = "ru") -> InlineKeyboardMarkup:
    buttons = []
    for ex in exercises:
        name = ex["name_ru"] if lang == "ru" else ex["name_en"]
        btn = InlineKeyboardButton(f"🗑️ {name}", callback_data=f"{Callback.DELETE_EXERCISE_CONFIRM}_{ex['id']}")
        buttons.append([btn])
    buttons.append([InlineKeyboardButton(t("back", lang), callback_data=Callback.BACK)])
    return InlineKeyboardMarkup(buttons)


def settings_keyboard(settings: dict, lang: str = "ru") -> InlineKeyboardMarkup:
    notif_status = t("notif_on", lang) if settings.get("notifications_enabled") else t("notif_off", lang)
    units_status = t("units_kg", lang) if settings.get("units") == "metric" else t("units_lb", lang)

    buttons = [
        [
            InlineKeyboardButton(t("lang_ru", lang), callback_data=Callback.SET_LANG_RU),
            InlineKeyboardButton(t("lang_en", lang), callback_data=Callback.SET_LANG_EN),
        ],
        [
            InlineKeyboardButton(t("units_kg", lang), callback_data=Callback.SET_UNITS_METRIC),
            InlineKeyboardButton(t("units_lb", lang), callback_data=Callback.SET_UNITS_IMPERIAL),
        ],
        [InlineKeyboardButton(notif_status, callback_data=Callback.SET_NOTIF)],
        [InlineKeyboardButton(t("back", lang), callback_data=Callback.BACK)],
    ]
    return InlineKeyboardMarkup(buttons)


def history_keyboard(workouts: list, page: int = 0, lang: str = "ru") -> InlineKeyboardMarkup:
    buttons = []
    for w in workouts:
        date = w["started_at"].strftime("%d.%m.%y") if w.get("started_at") else ""
        cat = w.get("category_name", "") or t("free_workout", lang)
        count = w.get("total_exercises", 0)
        btn = InlineKeyboardButton(
            f"📅 {date} - {cat} ({count})",
            callback_data=f"{Callback.WORKOUT}_{w['id']}"
        )
        buttons.append([btn])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(t("prev", lang), callback_data=f"{Callback.HISTORY_PAGE}_{page - 1}"))
    if len(workouts) == 10:
        nav_row.append(InlineKeyboardButton(t("next", lang), callback_data=f"{Callback.HISTORY_PAGE}_{page + 1}"))
    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(t("main_menu", lang), callback_data=Callback.MAIN_MENU)])
    return InlineKeyboardMarkup(buttons)


def workout_detail_keyboard(workout_id: int, page: int = 0, lang: str = "ru") -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(t("prev", lang), callback_data=f"{Callback.HISTORY_PAGE}_{page}"),
            InlineKeyboardButton(t("next", lang), callback_data=f"{Callback.HISTORY_PAGE}_{page}"),
        ],
        [InlineKeyboardButton(t("main_menu", lang), callback_data=Callback.MAIN_MENU)],
    ]
    return InlineKeyboardMarkup(buttons)


def back_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(t("back", lang), callback_data=Callback.BACK)]])
