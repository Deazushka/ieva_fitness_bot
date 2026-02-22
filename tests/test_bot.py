import pytest
from unittest.mock import MagicMock, AsyncMock
from telegram import Update, Message, User, CallbackQuery
from telegram.ext import ContextTypes

from src.handlers import Handlers
from src.constants import State, Callback, t
from src.keyboards import main_menu_keyboard


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.get_or_create_user = AsyncMock(return_value=1)
    db.get_user_settings = AsyncMock(return_value={"language": "ru", "units": "metric", "notifications_enabled": False})
    db.get_categories = AsyncMock(return_value=[
        {"id": 1, "name_ru": "День ног", "name_en": "Leg Day"},
        {"id": 2, "name_ru": "День рук", "name_en": "Arm Day"},
    ])
    db.get_exercises = AsyncMock(return_value=[
        {"id": 1, "name_ru": "Приседания", "name_en": "Squats"},
    ])
    db.start_workout = AsyncMock(return_value=1)
    db.get_active_workout = AsyncMock(return_value=None)
    db.add_workout_exercise = AsyncMock(return_value=1)
    db.get_user_workouts = AsyncMock(return_value=[])
    db.get_workout_stats = AsyncMock(return_value={"total_workouts": 0, "total_exercises": 0})
    return db


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 12345
    update.effective_user.username = "test_user"
    update.effective_user.first_name = "Test"
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.callback_query = MagicMock(spec=CallbackQuery)
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.answer = AsyncMock()
    update.callback_query.data = ""
    return update


@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    return context


@pytest.fixture
def handlers(mock_db):
    return Handlers(mock_db)


class TestConstants:
    def test_state_values(self):
        assert State.MAIN_MENU.value == 1
        assert State.CATEGORY_SELECT.value == 2
        assert State.EXERCISE_SELECT.value == 3

    def test_callback_constants(self):
        assert Callback.START_WORKOUT == "start_workout"
        assert Callback.BACK == "back"

    def test_translations(self):
        assert t("welcome", "ru") == "🏋️ Добро пожаловать!\nВыберите действие:"
        assert t("welcome", "en") == "🏋️ Welcome!\nSelect an action:"


class TestKeyboards:
    def test_main_menu_keyboard(self):
        keyboard = main_menu_keyboard("ru")
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) == 3

    def test_main_menu_keyboard_english(self):
        keyboard = main_menu_keyboard("en")
        assert keyboard is not None


class TestHandlers:
    @pytest.mark.asyncio
    async def test_start(self, handlers, mock_update, mock_context, mock_db):
        mock_update.callback_query = None

        result = await handlers.start(mock_update, mock_context)

        assert result == State.MAIN_MENU
        mock_db.get_or_create_user.assert_called_once()
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_back_to_main(self, handlers, mock_update, mock_context):
        mock_context.user_data["lang"] = "ru"

        result = await handlers.back_to_main(mock_update, mock_context)

        assert result == State.MAIN_MENU
        mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_workout(self, handlers, mock_update, mock_context, mock_db):
        mock_context.user_data["lang"] = "ru"

        result = await handlers.start_workout(mock_update, mock_context)

        assert result == State.CATEGORY_SELECT
        mock_db.get_categories.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_history_empty(self, handlers, mock_update, mock_context, mock_db):
        mock_context.user_data["lang"] = "ru"
        mock_context.user_data["user_id"] = 1

        result = await handlers.show_history(mock_update, mock_context)

        assert result == State.MAIN_MENU
        mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_settings(self, handlers, mock_update, mock_context, mock_db):
        mock_context.user_data["lang"] = "ru"
        mock_context.user_data["user_id"] = 1

        result = await handlers.show_settings(mock_update, mock_context)

        assert result == State.SETTINGS_MENU
        mock_db.get_user_settings.assert_called()
