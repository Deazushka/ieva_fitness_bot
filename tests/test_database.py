import pytest
import os
import sys
import tempfile
import sqlite3
import threading

os.environ['TESTING'] = '1'

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    old_environ = os.environ.copy()
    os.environ['DATABASE_PATH'] = path
    
    import config
    import database
    import importlib
    
    importlib.reload(config)
    importlib.reload(database)
    
    database._local = threading.local()
    
    yield database
    
    conn = getattr(database._local, 'connection', None)
    if conn:
        try:
            conn.close()
        except:
            pass
    
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass
    
    os.environ.clear()
    os.environ.update(old_environ)


class TestCategories:
    def test_get_categories_returns_list(self, temp_db):
        categories = temp_db.get_categories()
        assert isinstance(categories, list)
    
    def test_add_category(self, temp_db):
        result = temp_db.add_category("Test Category")
        assert result is not None
        
        categories = temp_db.get_categories()
        names = [cat[1] for cat in categories]
        assert "Test Category" in names
    
    def test_add_duplicate_category_ignored(self, temp_db):
        temp_db.add_category("Duplicate")
        result = temp_db.add_category("Duplicate")
        assert result is not None
    
    def test_delete_category(self, temp_db):
        temp_db.add_category("To Delete")
        result = temp_db.delete_category("To Delete")
        assert result is True
        
        categories = temp_db.get_categories()
        names = [cat[1] for cat in categories]
        assert "To Delete" not in names
    
    def test_delete_nonexistent_category(self, temp_db):
        result = temp_db.delete_category("Nonexistent")
        assert result is False
    
    def test_category_exists(self, temp_db):
        temp_db.add_category("Existing")
        assert temp_db.category_exists("Existing") is True
        assert temp_db.category_exists("Not Existing") is False


class TestExercises:
    def test_get_exercises_returns_list(self, temp_db):
        exercises = temp_db.get_exercises()
        assert isinstance(exercises, list)
    
    def test_add_exercise(self, temp_db):
        result = temp_db.add_exercise("Test Exercise")
        assert result is not None
        
        exercises = temp_db.get_exercises()
        names = [ex[1] for ex in exercises]
        assert "Test Exercise" in names
    
    def test_add_exercise_with_category(self, temp_db):
        temp_db.add_category("Test Cat")
        result = temp_db.add_exercise("Ex With Cat", "Test Cat")
        assert result is not None
    
    def test_delete_exercise(self, temp_db):
        temp_db.add_exercise("To Delete Ex")
        result = temp_db.delete_exercise("To Delete Ex")
        assert result is True
    
    def test_exercise_exists(self, temp_db):
        temp_db.add_exercise("Existing Ex")
        assert temp_db.exercise_exists("Existing Ex") is True


class TestWorkouts:
    def test_start_workout(self, temp_db):
        workout_id = temp_db.start_workout(12345, "test_user", "Test Category")
        assert workout_id is not None
        assert isinstance(workout_id, int)
    
    def test_get_active_workout(self, temp_db):
        workout_id = temp_db.start_workout(99999, "test_user", "Test Category")
        
        active = temp_db.get_active_workout(99999)
        assert active is not None
        assert active['workout_id'] == workout_id
        assert active['category'] == "Test Category"
    
    def test_get_active_workout_no_workout(self, temp_db):
        active = temp_db.get_active_workout(88888)
        assert active is None
    
    def test_add_exercise_to_workout(self, temp_db):
        workout_id = temp_db.start_workout(77777, "test_user", "Test Category")
        result = temp_db.add_exercise_to_workout(workout_id, "Push-ups", 3, "12", None)
        assert result is not None
    
    def test_finish_workout(self, temp_db):
        workout_id = temp_db.start_workout(66666, "test_user", "Test Category")
        result = temp_db.finish_workout(workout_id)
        assert result is True
        
        active = temp_db.get_active_workout(66666)
        assert active is None
    
    def test_cancel_workout(self, temp_db):
        workout_id = temp_db.start_workout(55555, "test_user", "Test Category")
        result = temp_db.cancel_workout(workout_id)
        assert result is True
        
        active = temp_db.get_active_workout(55555)
        assert active is None
    
    def test_get_user_workouts(self, temp_db):
        workout_id = temp_db.start_workout(44444, "test_user", "Test Category")
        temp_db.finish_workout(workout_id)
        
        workouts = temp_db.get_user_workouts(44444)
        assert len(workouts) >= 1
    
    def test_get_workout_details(self, temp_db):
        workout_id = temp_db.start_workout(33333, "test_user", "Test Category")
        temp_db.add_exercise_to_workout(workout_id, "Push-ups", 3, "12", None)
        temp_db.finish_workout(workout_id)
        
        details = temp_db.get_workout_details(workout_id)
        assert details is not None
        assert 'workout' in details
        assert 'exercises' in details
        assert len(details['exercises']) == 1
    
    def test_get_workout_stats(self, temp_db):
        workout_id = temp_db.start_workout(22222, "test_user", "Test Category")
        temp_db.add_exercise_to_workout(workout_id, "Push-ups", 3, "12", None)
        temp_db.finish_workout(workout_id)
        
        stats = temp_db.get_workout_stats(22222)
        assert stats['total_workouts'] >= 1
        assert stats['total_exercises'] >= 1
        assert stats['last_workout'] is not None


class TestUserSettings:
    def test_get_user_settings_default(self, temp_db):
        settings = temp_db.get_user_settings(999001)
        assert settings['user_id'] == 999001
        assert settings['language'] == 'ru'
        assert settings['units'] == 'metric'
    
    def test_update_user_settings(self, temp_db):
        temp_db.update_user_settings(999002, language='en', units='imperial')
        
        settings = temp_db.get_user_settings(999002)
        assert settings['language'] == 'en'
        assert settings['units'] == 'imperial'
    
    def test_set_language(self, temp_db):
        temp_db.set_language(999003, 'en')
        settings = temp_db.get_user_settings(999003)
        assert settings['language'] == 'en'
    
    def test_set_notifications(self, temp_db):
        temp_db.set_notifications(999004, True)
        settings = temp_db.get_user_settings(999004)
        assert settings['notifications_enabled'] is True


class TestUserSets:
    def test_get_user_sets_default(self, temp_db):
        user_sets = temp_db.get_user_sets(999101)
        assert isinstance(user_sets, list)
        assert len(user_sets) > 0
    
    def test_add_user_set(self, temp_db):
        result = temp_db.add_user_set(999102, "5x5", 5, "5", None)
        assert result is not None
        
        user_sets = temp_db.get_user_sets(999102)
        names = [s[1] for s in user_sets]
        assert "5x5" in names
    
    def test_delete_user_set(self, temp_db):
        temp_db.add_user_set(999103, "To Delete Set", 3, "10", None)
        result = temp_db.delete_user_set(999103, "To Delete Set")
        assert result is True
    
    def test_get_set_by_name(self, temp_db):
        temp_db.add_user_set(999104, "Test Set", 4, "8", 50.0)
        
        set_data = temp_db.get_set_by_name(999104, "Test Set")
        assert set_data is not None
        assert set_data[1] == "Test Set"


class TestExerciseSets:
    def test_add_exercise_set(self, temp_db):
        temp_db.add_exercise("Test Ex Unique 1")
        result = temp_db.add_exercise_set("Test Ex Unique 1", "3x12", 3, "12", None)
        assert result is not None
    
    def test_get_exercise_sets(self, temp_db):
        temp_db.add_exercise("Ex With Sets Unique")
        temp_db.add_exercise_set("Ex With Sets Unique", "3x10", 3, "10", None)
        
        sets = temp_db.get_exercise_sets("Ex With Sets Unique")
        assert len(sets) > 0
    
    def test_delete_exercise_set(self, temp_db):
        temp_db.add_exercise("Ex For Delete Unique")
        temp_db.add_exercise_set("Ex For Delete Unique", "ToDelete", 3, "10", None)
        
        result = temp_db.delete_exercise_set("Ex For Delete Unique", "ToDelete")
        assert result is True
