import sqlite3
from datetime import datetime
from config import DATABASE_PATH, logger

conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
cursor = conn.cursor()

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
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT,
    category_name TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    total_exercises INTEGER DEFAULT 0,
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

conn.commit()

DEFAULT_CATEGORIES = [
    "День ног",
    "День рук",
    "День спины",
    "День груди",
    "Свободная тренировка"
]

DEFAULT_EXERCISES = [
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

DEFAULT_SETS = [
    ("3x12", 3, "12", None),
    ("4x10", 4, "10", None),
    ("5x5", 5, "5", None),
    ("3x15", 3, "15", None),
    ("4x8", 4, "8", None),
]

def init_default_data():
    for cat in DEFAULT_CATEGORIES:
        cursor.execute("INSERT OR IGNORE INTO categories(name) VALUES(?)", (cat,))
    
    for ex in DEFAULT_EXERCISES:
        cursor.execute("INSERT OR IGNORE INTO exercises(name) VALUES(?)", (ex,))
    
    conn.commit()
    logger.info("Default data initialized")

def get_categories():
    return cursor.execute("SELECT id, name FROM categories ORDER BY name").fetchall()

def add_category(name):
    cursor.execute("INSERT OR IGNORE INTO categories(name) VALUES(?)", (name,))
    conn.commit()
    return cursor.lastrowid

def delete_category(name):
    cursor.execute("DELETE FROM categories WHERE name = ?", (name,))
    conn.commit()
    return cursor.rowcount > 0

def category_exists(name):
    result = cursor.execute("SELECT 1 FROM categories WHERE name = ?", (name,)).fetchone()
    return result is not None

def get_exercises():
    return cursor.execute("SELECT id, name, category_id FROM exercises ORDER BY name").fetchall()

def get_exercises_by_category(category_name):
    cat_id = cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,)).fetchone()
    if cat_id:
        return cursor.execute("SELECT id, name FROM exercises WHERE category_id = ? ORDER BY name", (cat_id[0],)).fetchall()
    return get_exercises()

def add_exercise(name, category_name=None):
    category_id = None
    if category_name:
        cat = cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,)).fetchone()
        if cat:
            category_id = cat[0]
    cursor.execute("INSERT OR IGNORE INTO exercises(name, category_id) VALUES(?, ?)", (name, category_id))
    conn.commit()
    return cursor.lastrowid

def delete_exercise(name):
    cursor.execute("DELETE FROM exercises WHERE name = ?", (name,))
    conn.commit()
    return cursor.rowcount > 0

def exercise_exists(name):
    result = cursor.execute("SELECT 1 FROM exercises WHERE name = ?", (name,)).fetchone()
    return result is not None

def start_workout(user_id, username, category_name):
    cursor.execute(
        "INSERT INTO workouts(user_id, username, category_name) VALUES(?, ?, ?)",
        (user_id, username, category_name)
    )
    conn.commit()
    logger.info(f"Workout started for user {user_id}, category: {category_name}")
    return cursor.lastrowid

def add_exercise_to_workout(workout_id, exercise_name, sets, reps, weight=None):
    cursor.execute(
        "INSERT INTO workout_exercises(workout_id, exercise_name, sets, reps, weight) VALUES(?, ?, ?, ?, ?)",
        (workout_id, exercise_name, sets, reps, weight)
    )
    
    cursor.execute("UPDATE workouts SET total_exercises = total_exercises + 1 WHERE id = ?", (workout_id,))
    conn.commit()
    logger.info(f"Exercise {exercise_name} added to workout {workout_id}")
    return cursor.lastrowid

def finish_workout(workout_id):
    cursor.execute(
        "UPDATE workouts SET finished_at = CURRENT_TIMESTAMP WHERE id = ?",
        (workout_id,)
    )
    conn.commit()
    logger.info(f"Workout {workout_id} finished")

def cancel_workout(workout_id):
    cursor.execute("DELETE FROM workout_exercises WHERE workout_id = ?", (workout_id,))
    cursor.execute("DELETE FROM workouts WHERE id = ?", (workout_id,))
    conn.commit()
    logger.info(f"Workout {workout_id} cancelled")

def get_user_workouts(user_id, limit=10):
    return cursor.execute("""
        SELECT id, category_name, started_at, finished_at, total_exercises 
        FROM workouts 
        WHERE user_id = ? AND finished_at IS NOT NULL
        ORDER BY started_at DESC 
        LIMIT ?
    """, (user_id, limit)).fetchall()

def get_workout_details(workout_id):
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

def get_workout_stats(user_id):
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

def get_user_settings(user_id):
    settings = cursor.execute("""
        SELECT user_id, language, units, notifications_enabled, notification_time
        FROM user_settings WHERE user_id = ?
    """, (user_id,)).fetchone()
    
    if not settings:
        cursor.execute("""
            INSERT INTO user_settings(user_id) VALUES(?)
        """, (user_id,))
        conn.commit()
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

def update_user_settings(user_id, **kwargs):
    allowed_keys = ['language', 'units', 'notifications_enabled', 'notification_time']
    updates = []
    values = []
    
    for key, value in kwargs.items():
        if key in allowed_keys:
            updates.append(f"{key} = ?")
            values.append(value)
    
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(user_id)
        cursor.execute(f"""
            UPDATE user_settings SET {', '.join(updates)} WHERE user_id = ?
        """, values)
        conn.commit()
        logger.info(f"Settings updated for user {user_id}")

def set_language(user_id, language):
    update_user_settings(user_id, language=language)

def set_units(user_id, units):
    update_user_settings(user_id, units=units)

def set_notifications(user_id, enabled, time=None):
    update_user_settings(user_id, notifications_enabled=int(enabled))
    if time:
        update_user_settings(user_id, notification_time=time)

def get_user_sets(user_id):
    user_sets = cursor.execute("""
        SELECT id, name, sets, reps, weight FROM workout_sets 
        WHERE user_id = ? ORDER BY created_at
    """, (user_id,)).fetchall()
    
    if not user_sets:
        for name, sets, reps, weight in DEFAULT_SETS:
            cursor.execute("""
                INSERT INTO workout_sets(user_id, name, sets, reps, weight) VALUES(?, ?, ?, ?, ?)
            """, (user_id, name, sets, reps, weight))
        conn.commit()
        user_sets = cursor.execute("""
            SELECT id, name, sets, reps, weight FROM workout_sets 
            WHERE user_id = ? ORDER BY created_at
        """, (user_id,)).fetchall()
        logger.info(f"Default sets initialized for user {user_id}")
    
    return user_sets

def add_user_set(user_id, name, sets, reps, weight=None):
    cursor.execute("""
        INSERT OR IGNORE INTO workout_sets(user_id, name, sets, reps, weight) 
        VALUES(?, ?, ?, ?, ?)
    """, (user_id, name, sets, reps, weight))
    conn.commit()
    logger.info(f"Set '{name}' added for user {user_id}")
    return cursor.lastrowid

def delete_user_set(user_id, name):
    cursor.execute("""
        DELETE FROM workout_sets WHERE user_id = ? AND name = ?
    """, (user_id, name))
    conn.commit()
    deleted = cursor.rowcount > 0
    if deleted:
        logger.info(f"Set '{name}' deleted for user {user_id}")
    return deleted

def get_set_by_name(user_id, name):
    result = cursor.execute("""
        SELECT id, name, sets, reps, weight FROM workout_sets 
        WHERE user_id = ? AND name = ?
    """, (user_id, name)).fetchone()
    return result

init_default_data()
