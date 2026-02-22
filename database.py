import sqlite3
import threading
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from contextlib import contextmanager
from config import DATABASE_PATH, logger

_local = threading.local()


def get_connection() -> sqlite3.Connection:
    if not hasattr(_local, 'connection') or _local.connection is None:
        _local.connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        _local.connection.row_factory = sqlite3.Row
    return _local.connection


@contextmanager
def get_cursor():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise


def init_database():
    with get_cursor() as cursor:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercise_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exercise_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            sets INTEGER,
            reps TEXT,
            weight REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (exercise_id) REFERENCES exercises(id),
            UNIQUE(exercise_id, name)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            category_name TEXT NOT NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            finished_at TIMESTAMP,
            total_exercises INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            notes TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS workout_exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_id INTEGER NOT NULL,
            exercise_name TEXT NOT NULL,
            sets INTEGER,
            reps TEXT,
            weight REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (workout_id) REFERENCES workouts(id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            language TEXT DEFAULT 'ru',
            units TEXT DEFAULT 'metric',
            notifications_enabled INTEGER DEFAULT 0,
            notification_time TEXT DEFAULT '09:00',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS workout_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            sets INTEGER,
            reps TEXT,
            weight REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_settings(user_id),
            UNIQUE(user_id, name)
        )
        """)
    
    logger.info("Database initialized successfully")


DEFAULT_CATEGORIES: List[str] = [
    "День ног",
    "День рук",
    "День спины",
    "День груди",
    "Свободная тренировка"
]

DEFAULT_EXERCISES: List[str] = [
    "Приседания",
    "Жим лёжа",
    "Становая тяга",
    "Подтягивания",
    "Отжимания",
    "Тяга штанги в наклоне",
    "Сгибание на бицепс",
    "Разгибание на трицепс",
    "Подъёмы на носки",
    "Планка"
]

DEFAULT_EXERCISE_SETS: List[Tuple[str, str, int, str, Optional[float]]] = [
    ("Приседания", "3x12", 3, "12", None),
    ("Приседания", "5x5", 5, "5", None),
    ("Жим лёжа", "3x12", 3, "12", None),
    ("Жим лёжа", "4x10", 4, "10", None),
    ("Становая тяга", "5x5", 5, "5", None),
    ("Подтягивания", "3x10", 3, "10", None),
    ("Отжимания", "3x15", 3, "15", None),
    ("Тяга штанги в наклоне", "4x10", 4, "10", None),
    ("Сгибание на бицепс", "3x12", 3, "12", None),
    ("Разгибание на трицепс", "3x12", 3, "12", None),
]

DEFAULT_SETS: List[Tuple[str, int, str, Optional[float]]] = [
    ("3x12", 3, "12", None),
    ("4x10", 4, "10", None),
    ("5x5", 5, "5", None),
    ("3x15", 3, "15", None),
    ("4x8", 4, "8", None),
]


def init_default_data() -> None:
    try:
        with get_cursor() as cursor:
            for cat in DEFAULT_CATEGORIES:
                cursor.execute("INSERT OR IGNORE INTO categories(name) VALUES(?)", (cat,))
            
            for ex in DEFAULT_EXERCISES:
                cursor.execute("INSERT OR IGNORE INTO exercises(name) VALUES(?)", (ex,))
            
            for exercise_name, set_name, sets, reps, weight in DEFAULT_EXERCISE_SETS:
                ex_id = cursor.execute("SELECT id FROM exercises WHERE name = ?", (exercise_name,)).fetchone()
                if ex_id:
                    cursor.execute("""
                        INSERT OR IGNORE INTO exercise_sets(exercise_id, name, sets, reps, weight) 
                        VALUES(?, ?, ?, ?, ?)
                    """, (ex_id[0], set_name, sets, reps, weight))
        
        logger.info("Default data initialized")
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize default data: {e}")


def get_categories() -> List[Tuple[int, str]]:
    with get_cursor() as cursor:
        return cursor.execute("SELECT id, name FROM categories ORDER BY name").fetchall()


def add_category(name: str) -> Optional[int]:
    try:
        with get_cursor() as cursor:
            cursor.execute("INSERT OR IGNORE INTO categories(name) VALUES(?)", (name,))
            return cursor.lastrowid
    except sqlite3.Error as e:
        logger.error(f"Failed to add category '{name}': {e}")
        return None


def delete_category(name: str) -> bool:
    try:
        with get_cursor() as cursor:
            cursor.execute("DELETE FROM categories WHERE name = ?", (name,))
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Failed to delete category '{name}': {e}")
        return False


def category_exists(name: str) -> bool:
    with get_cursor() as cursor:
        result = cursor.execute("SELECT 1 FROM categories WHERE name = ?", (name,)).fetchone()
        return result is not None


def get_exercises() -> List[Tuple[int, str, Optional[int]]]:
    with get_cursor() as cursor:
        return cursor.execute("SELECT id, name, category_id FROM exercises ORDER BY name").fetchall()


def get_exercises_by_category(category_name: str) -> List[Tuple[int, str, Optional[int]]]:
    with get_cursor() as cursor:
        cat_id = cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,)).fetchone()
        
        if category_name == "Свободная тренировка" or not cat_id:
            return cursor.execute("""
                SELECT id, name, category_id FROM exercises 
                WHERE category_id IS NULL 
                ORDER BY name
            """).fetchall()
        
        category_exercises = cursor.execute("""
            SELECT id, name, category_id FROM exercises 
            WHERE category_id = ? 
            ORDER BY name
        """, (cat_id[0],)).fetchall()
        
        if not category_exercises:
            return cursor.execute("""
                SELECT id, name, category_id FROM exercises 
                WHERE category_id IS NULL 
                ORDER BY name
            """).fetchall()
        
        return category_exercises


def add_exercise(name: str, category_name: Optional[str] = None) -> Optional[int]:
    try:
        with get_cursor() as cursor:
            category_id = None
            if category_name:
                cat = cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,)).fetchone()
                if cat:
                    category_id = cat[0]
            cursor.execute("INSERT OR IGNORE INTO exercises(name, category_id) VALUES(?, ?)", (name, category_id))
            return cursor.lastrowid
    except sqlite3.Error as e:
        logger.error(f"Failed to add exercise '{name}': {e}")
        return None


def delete_exercise(name: str) -> bool:
    try:
        with get_cursor() as cursor:
            cursor.execute("DELETE FROM exercises WHERE name = ?", (name,))
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Failed to delete exercise '{name}': {e}")
        return False


def exercise_exists(name: str) -> bool:
    with get_cursor() as cursor:
        result = cursor.execute("SELECT 1 FROM exercises WHERE name = ?", (name,)).fetchone()
        return result is not None


def get_exercise_by_name(name: str) -> Optional[Tuple[int, str, Optional[int]]]:
    with get_cursor() as cursor:
        return cursor.execute("SELECT id, name, category_id FROM exercises WHERE name = ?", (name,)).fetchone()


def get_exercise_sets(exercise_name: str) -> List[Tuple[int, int, str, int, str, Optional[float]]]:
    with get_cursor() as cursor:
        ex_id = cursor.execute("SELECT id FROM exercises WHERE name = ?", (exercise_name,)).fetchone()
        if ex_id:
            return cursor.execute("""
                SELECT id, exercise_id, name, sets, reps, weight FROM exercise_sets 
                WHERE exercise_id = ? ORDER BY created_at
            """, (ex_id[0],)).fetchall()
        return []


def add_exercise_set(exercise_name: str, set_name: str, sets: int, reps: str, weight: Optional[float] = None) -> Optional[int]:
    try:
        with get_cursor() as cursor:
            ex_id = cursor.execute("SELECT id FROM exercises WHERE name = ?", (exercise_name,)).fetchone()
            if ex_id:
                cursor.execute("""
                    INSERT OR IGNORE INTO exercise_sets(exercise_id, name, sets, reps, weight) 
                    VALUES(?, ?, ?, ?, ?)
                """, (ex_id[0], set_name, sets, reps, weight))
                logger.info(f"Set '{set_name}' added to exercise '{exercise_name}'")
                return cursor.lastrowid
            return None
    except sqlite3.Error as e:
        logger.error(f"Failed to add exercise set: {e}")
        return None


def delete_exercise_set(exercise_name: str, set_name: str) -> bool:
    try:
        with get_cursor() as cursor:
            ex_id = cursor.execute("SELECT id FROM exercises WHERE name = ?", (exercise_name,)).fetchone()
            if ex_id:
                cursor.execute("""
                    DELETE FROM exercise_sets WHERE exercise_id = ? AND name = ?
                """, (ex_id[0], set_name))
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"Set '{set_name}' deleted from exercise '{exercise_name}'")
                return deleted
            return False
    except sqlite3.Error as e:
        logger.error(f"Failed to delete exercise set: {e}")
        return False


def get_exercise_set_by_name(exercise_name: str, set_name: str) -> Optional[Tuple[int, int, str, int, str, Optional[float]]]:
    with get_cursor() as cursor:
        ex_id = cursor.execute("SELECT id FROM exercises WHERE name = ?", (exercise_name,)).fetchone()
        if ex_id:
            return cursor.execute("""
                SELECT id, exercise_id, name, sets, reps, weight FROM exercise_sets 
                WHERE exercise_id = ? AND name = ?
            """, (ex_id[0], set_name)).fetchone()
        return None


def start_workout(user_id: int, username: str, category_name: str) -> Optional[int]:
    try:
        with get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO workouts(user_id, username, category_name, is_active) VALUES(?, ?, ?, 1)",
                (user_id, username, category_name)
            )
            workout_id = cursor.lastrowid
            logger.info(f"Workout started for user {user_id}, category: {category_name}")
            return workout_id
    except sqlite3.Error as e:
        logger.error(f"Failed to start workout: {e}")
        return None


def get_active_workout(user_id: int) -> Optional[Dict[str, Any]]:
    with get_cursor() as cursor:
        result = cursor.execute("""
            SELECT id, user_id, username, category_name, started_at, total_exercises
            FROM workouts 
            WHERE user_id = ? AND is_active = 1 AND finished_at IS NULL
            ORDER BY started_at DESC LIMIT 1
        """, (user_id,)).fetchone()
        
        if result:
            return {
                'workout_id': result[0],
                'user_id': result[1],
                'username': result[2],
                'category': result[3],
                'started_at': result[4],
                'total_exercises': result[5]
            }
        return None


def add_exercise_to_workout(workout_id: int, exercise_name: str, sets: int, reps: str, weight: Optional[float] = None) -> Optional[int]:
    try:
        with get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO workout_exercises(workout_id, exercise_name, sets, reps, weight) VALUES(?, ?, ?, ?, ?)",
                (workout_id, exercise_name, sets, reps, weight)
            )
            
            cursor.execute("UPDATE workouts SET total_exercises = total_exercises + 1 WHERE id = ?", (workout_id,))
            logger.info(f"Exercise {exercise_name} added to workout {workout_id}")
            return cursor.lastrowid
    except sqlite3.Error as e:
        logger.error(f"Failed to add exercise to workout: {e}")
        return None


def finish_workout(workout_id: int) -> bool:
    try:
        with get_cursor() as cursor:
            cursor.execute(
                "UPDATE workouts SET finished_at = CURRENT_TIMESTAMP, is_active = 0 WHERE id = ?",
                (workout_id,)
            )
            logger.info(f"Workout {workout_id} finished")
            return True
    except sqlite3.Error as e:
        logger.error(f"Failed to finish workout: {e}")
        return False


def cancel_workout(workout_id: int) -> bool:
    try:
        with get_cursor() as cursor:
            cursor.execute("DELETE FROM workout_exercises WHERE workout_id = ?", (workout_id,))
            cursor.execute("DELETE FROM workouts WHERE id = ?", (workout_id,))
            logger.info(f"Workout {workout_id} cancelled")
            return True
    except sqlite3.Error as e:
        logger.error(f"Failed to cancel workout: {e}")
        return False


def get_user_workouts(user_id: int, limit: int = 10) -> List[Tuple[int, str, str, str, int]]:
    with get_cursor() as cursor:
        return cursor.execute("""
            SELECT id, category_name, started_at, finished_at, total_exercises 
            FROM workouts 
            WHERE user_id = ? AND finished_at IS NOT NULL
            ORDER BY started_at DESC 
            LIMIT ?
        """, (user_id, limit)).fetchall()


def get_workout_details(workout_id: int) -> Optional[Dict[str, Any]]:
    with get_cursor() as cursor:
        workout = cursor.execute("""
            SELECT id, user_id, username, category_name, started_at, finished_at, total_exercises, notes
            FROM workouts WHERE id = ?
        """, (workout_id,)).fetchone()
        
        if not workout:
            return None
        
        exercises = cursor.execute("""
            SELECT exercise_name, sets, reps, weight, notes
            FROM workout_exercises WHERE workout_id = ?
        """, (workout_id,)).fetchall()
        
        return {
            'workout': workout,
            'exercises': exercises
        }


def get_workout_stats(user_id: int) -> Dict[str, Any]:
    with get_cursor() as cursor:
        total_workouts = cursor.execute("""
            SELECT COUNT(*) FROM workouts WHERE user_id = ? AND finished_at IS NOT NULL
        """, (user_id,)).fetchone()[0]
        
        total_exercises = cursor.execute("""
            SELECT SUM(total_exercises) FROM workouts WHERE user_id = ? AND finished_at IS NOT NULL
        """, (user_id,)).fetchone()[0] or 0
        
        last_workout = cursor.execute("""
            SELECT started_at FROM workouts 
            WHERE user_id = ? AND finished_at IS NOT NULL
            ORDER BY started_at DESC LIMIT 1
        """, (user_id,)).fetchone()
        
        return {
            'total_workouts': total_workouts,
            'total_exercises': total_exercises,
            'last_workout': last_workout[0] if last_workout else None
        }


def get_user_settings(user_id: int) -> Dict[str, Any]:
    with get_cursor() as cursor:
        settings = cursor.execute("""
            SELECT user_id, language, units, notifications_enabled, notification_time
            FROM user_settings WHERE user_id = ?
        """, (user_id,)).fetchone()
        
        if not settings:
            cursor.execute("""
                INSERT INTO user_settings(user_id) VALUES(?)
            """, (user_id,))
            settings = cursor.execute("""
                SELECT user_id, language, units, notifications_enabled, notification_time
                FROM user_settings WHERE user_id = ?
            """, (user_id,)).fetchone()
        
        return {
            'user_id': settings[0],
            'language': settings[1],
            'units': settings[2],
            'notifications_enabled': bool(settings[3]),
            'notification_time': settings[4]
        }


SETTINGS_ALLOWED_KEYS = {'language', 'units', 'notifications_enabled', 'notification_time'}


def update_user_settings(user_id: int, **kwargs: Any) -> bool:
    updates = []
    values = []
    
    for key, value in kwargs.items():
        if key in SETTINGS_ALLOWED_KEYS:
            updates.append(f"{key} = ?")
            values.append(value)
    
    if not updates:
        return False
    
    try:
        with get_cursor() as cursor:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(user_id)
            cursor.execute(
                f"UPDATE user_settings SET {', '.join(updates)} WHERE user_id = ?",
                values
            )
            logger.info(f"Settings updated for user {user_id}")
            return True
    except sqlite3.Error as e:
        logger.error(f"Failed to update settings: {e}")
        return False


def set_language(user_id: int, language: str) -> bool:
    return update_user_settings(user_id, language=language)


def set_units(user_id: int, units: str) -> bool:
    return update_user_settings(user_id, units=units)


def set_notifications(user_id: int, enabled: bool, time: Optional[str] = None) -> bool:
    result = update_user_settings(user_id, notifications_enabled=int(enabled))
    if time:
        update_user_settings(user_id, notification_time=time)
    return result


def get_user_sets(user_id: int) -> List[Tuple[int, str, int, str, Optional[float]]]:
    with get_cursor() as cursor:
        user_sets = cursor.execute("""
            SELECT id, name, sets, reps, weight FROM workout_sets 
            WHERE user_id = ? ORDER BY created_at
        """, (user_id,)).fetchall()
        
        if not user_sets:
            for name, sets, reps, weight in DEFAULT_SETS:
                cursor.execute("""
                    INSERT INTO workout_sets(user_id, name, sets, reps, weight) VALUES(?, ?, ?, ?, ?)
                """, (user_id, name, sets, reps, weight))
            user_sets = cursor.execute("""
                SELECT id, name, sets, reps, weight FROM workout_sets 
                WHERE user_id = ? ORDER BY created_at
            """, (user_id,)).fetchall()
            logger.info(f"Default sets initialized for user {user_id}")
        
        return user_sets


def add_user_set(user_id: int, name: str, sets: int, reps: str, weight: Optional[float] = None) -> Optional[int]:
    try:
        with get_cursor() as cursor:
            cursor.execute("""
                INSERT OR IGNORE INTO workout_sets(user_id, name, sets, reps, weight) 
                VALUES(?, ?, ?, ?, ?)
            """, (user_id, name, sets, reps, weight))
            logger.info(f"Set '{name}' added for user {user_id}")
            return cursor.lastrowid
    except sqlite3.Error as e:
        logger.error(f"Failed to add user set: {e}")
        return None


def delete_user_set(user_id: int, name: str) -> bool:
    try:
        with get_cursor() as cursor:
            cursor.execute("""
                DELETE FROM workout_sets WHERE user_id = ? AND name = ?
            """, (user_id, name))
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Set '{name}' deleted for user {user_id}")
            return deleted
    except sqlite3.Error as e:
        logger.error(f"Failed to delete user set: {e}")
        return False


def get_set_by_name(user_id: int, name: str) -> Optional[Tuple[int, str, int, str, Optional[float]]]:
    with get_cursor() as cursor:
        return cursor.execute("""
            SELECT id, name, sets, reps, weight FROM workout_sets 
            WHERE user_id = ? AND name = ?
        """, (user_id, name)).fetchone()


init_database()
init_default_data()
