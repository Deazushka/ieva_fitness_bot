import aiosqlite
import datetime
from config import DB_PATH


async def create_tables():
    """Создает необходимые таблицы в БД."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            tg_id INTEGER UNIQUE,
            username TEXT,
            settings TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            name TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY,
            category_id INTEGER,
            user_id INTEGER,
            name TEXT,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            category_id INTEGER,
            started_at DATETIME,
            finished_at DATETIME,
            is_active BOOLEAN
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS workout_exercises (
            id INTEGER PRIMARY KEY,
            workout_id INTEGER,
            exercise_id INTEGER,
            reps INTEGER,
            weight REAL,
            created_at DATETIME
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_presets (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            exercise_id INTEGER,
            reps INTEGER,
            weight REAL,
            last_used_at DATETIME,
            UNIQUE(user_id, exercise_id, reps, weight)
        )
        """)

        # Заполнение базовых категорий и упражнений, если таблица пуста
        cursor = await db.execute("SELECT COUNT(*) FROM categories")
        count = await cursor.fetchone()
        if count[0] == 0:
            categories = [
                (1, None, "День ног"),
                (2, None, "День рук"),
            ]
            await db.executemany(
                "INSERT INTO categories (id, user_id, name) VALUES (?, ?, ?)",
                categories,
            )

            exercises = [
                # День ног
                (None, 1, None, "Румынская тяга"),
                (None, 1, None, "Ягодичный мост"),
                (None, 1, None, "Жим ногами"),
                (None, 1, None, "Разведение ног"),
                (None, 1, None, "Сведение ног"),
                (None, 1, None, "Приседание плие"),
                (None, 1, None, "Сгибание лежа"),
                (None, 1, None, "Сгибание сидя"),
                # День рук
                (None, 2, None, "Отжимания в смите"),
                (None, 2, None, "Тяга в кроссовере"),
                (None, 2, None, "Суперсет"),
                (None, 2, None, "Хаммер"),
                (None, 2, None, "Плечи"),
                (None, 2, None, "Бицепс"),
                (None, 2, None, "Трицепс"),
                (None, 2, None, "Тяга верхнего блока"),
                (None, 2, None, "Жим на наклонной скамье"),
                (None, 2, None, "Подъемы гантелей"),
                (None, 2, None, "Подъемы блина"),
                (None, 2, None, "Скручивание на пресс"),
            ]
            await db.executemany(
                "INSERT INTO exercises (id, category_id, user_id, name) VALUES (?, ?, ?, ?)",
                exercises,
            )

        await db.commit()


async def get_or_create_user(tg_id: int, username: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id FROM users WHERE tg_id = ?", (tg_id,)
        ) as cursor:
            user = await cursor.fetchone()
            if user:
                return user["id"]

            await db.execute(
                "INSERT INTO users (tg_id, username) VALUES (?, ?)", (tg_id, username)
            )
            await db.commit()

            async with db.execute(
                "SELECT id FROM users WHERE tg_id = ?", (tg_id,)
            ) as cursor:
                new_user = await cursor.fetchone()
                return new_user["id"]


async def get_categories(user_id: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM categories WHERE user_id IS NULL"
        params = []
        if user_id:
            query += " OR user_id = ?"
            params.append(user_id)

        async with db.execute(query, params) as cursor:
            return await cursor.fetchall()

async def add_category(user_id: int, name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO categories (user_id, name) VALUES (?, ?)", (user_id, name)
        )
        await db.commit()

async def delete_category(user_id: int, name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM categories WHERE user_id = ? AND name = ?", (user_id, name)
        )
        await db.commit()


async def get_category_by_id(cat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM categories WHERE id = ?", (cat_id,)
        ) as cursor:
            return await cursor.fetchone()


async def get_exercises(category_id: int, user_id: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM exercises WHERE category_id = ? AND (user_id IS NULL"
        params = [category_id]
        if user_id:
            query += " OR user_id = ?)"
            params.append(user_id)
        else:
            query += ")"
        async with db.execute(query, params) as cursor:
            return await cursor.fetchall()

async def add_exercise(category_id: int, user_id: int, name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO exercises (category_id, user_id, name) VALUES (?, ?, ?)",
            (category_id, user_id, name)
        )
        await db.commit()

async def delete_exercise(category_id: int, user_id: int, name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM exercises WHERE category_id = ? AND user_id = ? AND name = ?",
            (category_id, user_id, name)
        )
        await db.commit()


async def get_exercise_by_id(ex_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM exercises WHERE id = ?", (ex_id,)
        ) as cursor:
            return await cursor.fetchone()


async def start_workout(user_id: int, category_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        # Удаляем (или помечаем закрытой) старую активную тренировку
        await db.execute(
            "DELETE FROM workouts WHERE user_id = ? AND is_active = 1", (user_id,)
        )

        now = datetime.datetime.now()
        await db.execute(
            "INSERT INTO workouts (user_id, category_id, started_at, is_active) VALUES (?, ?, ?, 1)",
            (user_id, category_id, now),
        )
        await db.commit()

        async with db.execute(
            "SELECT id FROM workouts WHERE user_id = ? AND is_active = 1", (user_id,)
        ) as cursor:
            workout = await cursor.fetchone()
            return workout[0] if workout else None


async def discard_active_workout(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM workouts WHERE user_id = ? AND is_active = 1", (user_id,)
        )
        await db.commit()


async def get_active_workout(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM workouts WHERE user_id = ? AND is_active = 1", (user_id,)
        ) as cursor:
            return await cursor.fetchone()


async def save_set(
    workout_id: int, user_id: int, exercise_id: int, reps: int, weight: float = None
):
    now = datetime.datetime.now()
    async with aiosqlite.connect(DB_PATH) as db:
        # Сохраняем подход
        await db.execute(
            "INSERT INTO workout_exercises (workout_id, exercise_id, reps, weight, created_at) VALUES (?, ?, ?, ?, ?)",
            (workout_id, exercise_id, reps, weight, now),
        )

        preset_weight = weight if weight is not None else 0.0
        # Обновляем/создаем пресет
        await db.execute(
            """
            INSERT INTO user_presets (user_id, exercise_id, reps, weight, last_used_at) 
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, exercise_id, reps, weight) 
            DO UPDATE SET last_used_at=excluded.last_used_at
        """,
            (user_id, exercise_id, reps, preset_weight, now),
        )

        await db.commit()


async def get_user_presets(user_id: int, exercise_id: int, limit: int = 4):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT reps, weight FROM user_presets WHERE user_id = ? AND exercise_id = ? ORDER BY last_used_at DESC LIMIT ?",
            (user_id, exercise_id, limit),
        ) as cursor:
            return await cursor.fetchall()


async def finish_workout(workout_id: int):
    now = datetime.datetime.now()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE workouts SET is_active = 0, finished_at = ? WHERE id = ?",
            (now, workout_id),
        )
        await db.commit()


async def get_workout_stats(workout_id: int):
    """Возвращает статистику для summary."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # Упражнения и подходы
        query = """
            SELECT e.name as exercise_name, we.reps, we.weight 
            FROM workout_exercises we
            JOIN exercises e ON we.exercise_id = e.id
            WHERE we.workout_id = ?
            ORDER BY we.created_at ASC
        """
        async with db.execute(query, (workout_id,)) as cursor:
            rows = await cursor.fetchall()

        stats = {}
        total_exercises = set()
        for r in rows:
            name = r["exercise_name"]
            total_exercises.add(name)
            if name not in stats:
                stats[name] = []

            w_str = f" ({r['weight']} кг)" if r["weight"] else ""
            stats[name].append(f"{r['reps']}{w_str}")

        # Форматирование
        lines = []
        for name, sets in stats.items():
            lines.append(f"• {name} — {len(sets)}x ({', '.join(sets)})")

        return len(total_exercises), "\n".join(lines)


async def get_workouts_history(user_id: int, limit: int = 50, offset: int = 0):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = """
            SELECT w.id, w.started_at, c.name as category_name 
            FROM workouts w
            JOIN categories c ON w.category_id = c.id
            WHERE w.user_id = ? AND w.is_active = 0
            ORDER BY w.started_at DESC
            LIMIT ? OFFSET ?
        """
        async with db.execute(query, (user_id, limit, offset)) as cursor:
            return await cursor.fetchall()


async def get_workouts_history_count(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM workouts WHERE user_id = ? AND is_active = 0",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def get_workout_details(workout_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = """
            SELECT w.started_at, c.name as category_name 
            FROM workouts w
            JOIN categories c ON w.category_id = c.id
            WHERE w.id = ?
        """
        async with db.execute(query, (workout_id,)) as cursor:
            workout = await cursor.fetchone()

        if not workout:
            return None

        # Упражнения
        total_ex, sets_str = await get_workout_stats(workout_id)

        return {
            "started_at": workout["started_at"],
            "category_name": workout["category_name"],
            "total_exercises": total_ex,
            "sets_str": sets_str,
        }
