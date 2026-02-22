import pytest
from unittest.mock import MagicMock, AsyncMock
from telegram import Update, Message, User
from telegram.ext import ContextTypes

from src.handlers import Handlers


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.get_or_create_user = AsyncMock(return_value=1)
    db.add_workout = AsyncMock(return_value=1)
    db.get_user_workouts = AsyncMock(return_value=[])
    db.get_workout_stats = AsyncMock(return_value={'total_workouts': 0, 'unique_exercises': 0})
    return db


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 12345
    update.effective_user.username = 'test_user'
    update.effective_user.first_name = 'Test'
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    return context


@pytest.fixture
def handlers(mock_db):
    return Handlers(mock_db)


class TestHandlers:
    @pytest.mark.asyncio
    async def test_help_command(self, handlers, mock_update, mock_context):
        await handlers.help(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert '/start' in call_args[0][0]
        assert '/log' in call_args[0][0]

    def test_parse_workout(self, handlers):
        sets, reps, weight = handlers._parse_workout('bench press 3x10 60')
        assert sets == 3
        assert reps == 10
        assert weight == 60

    def test_parse_workout_no_weight(self, handlers):
        sets, reps, weight = handlers._parse_workout('pull ups 3x12')
        assert sets == 3
        assert reps == 12
        assert weight is None

    def test_extract_exercise(self, handlers):
        exercise = handlers._extract_exercise('bench press 3x10 60')
        assert exercise == 'bench press'

    def test_extract_exercise_complex(self, handlers):
        exercise = handlers._extract_exercise('incline dumbbell press 4x12 22.5kg')
        assert 'incline' in exercise
        assert 'dumbbell' in exercise
        assert 'press' in exercise

    @pytest.mark.asyncio
    async def test_start_command(self, handlers, mock_update, mock_context, mock_db):
        await handlers.start(mock_update, mock_context)

        mock_db.get_or_create_user.assert_called_once_with(12345, 'test_user')
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_workout(self, handlers, mock_update, mock_context, mock_db):
        mock_context.args = ['bench', 'press', '3x10', '60']

        await handlers.log_workout(mock_update, mock_context)

        mock_db.add_workout.assert_called_once()
        mock_update.message.reply_text.assert_called_once()
