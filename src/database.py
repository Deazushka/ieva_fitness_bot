import asyncpg
import asyncpg.exceptions
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from .constants import DEFAULT_CATEGORIES, DEFAULT_EXERCISES, DEFAULT_SETS

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(self.database_url, min_size=2, max_size=10)
        await self._create_tables()
        await self._init_default_data()
        logger.info("Connected to PostgreSQL")

    async def disconnect(self) -> None:
        if self._pool:
            await self._pool.close()

    async def _create_tables(self) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY REFERENCES users(id),
                    language TEXT DEFAULT 'ru',
                    units TEXT DEFAULT 'metric',
                    notifications_enabled BOOLEAN DEFAULT FALSE
                );

                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    name_ru TEXT UNIQUE NOT NULL,
                    name_en TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS exercises (
                    id SERIAL PRIMARY KEY,
                    name_ru TEXT NOT NULL,
                    name_en TEXT NOT NULL,
                    category_id INTEGER REFERENCES categories(id),
                    UNIQUE(name_ru, name_en)
                );

                CREATE TABLE IF NOT EXISTS exercise_sets (
                    id SERIAL PRIMARY KEY,
                    exercise_id INTEGER REFERENCES exercises(id),
                    name TEXT NOT NULL,
                    sets INTEGER NOT NULL,
                    reps INTEGER NOT NULL,
                    weight REAL
                );

                CREATE TABLE IF NOT EXISTS workouts (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    category_name TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    finished_at TIMESTAMP,
                    total_exercises INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS workout_exercises (
                    id SERIAL PRIMARY KEY,
                    workout_id INTEGER NOT NULL REFERENCES workouts(id),
                    exercise_name TEXT NOT NULL,
                    sets INTEGER,
                    reps INTEGER,
                    weight REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS workout_sets (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    name TEXT NOT NULL,
                    sets INTEGER NOT NULL,
                    reps INTEGER NOT NULL,
                    weight REAL
                );
            ''')
            
            for col, col_type in [
                ("category_name", "TEXT"),
                ("started_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
                ("finished_at", "TIMESTAMP"),
                ("is_active", "BOOLEAN DEFAULT TRUE"),
                ("total_exercises", "INTEGER DEFAULT 0"),
            ]:
                try:
                    await conn.execute(f"ALTER TABLE workouts ADD COLUMN {col} {col_type}")
                except asyncpg.exceptions.DuplicateColumnError:
                    pass

    async def _init_default_data(self) -> None:
        async with self._pool.acquire() as conn:
            for name_ru, name_en in DEFAULT_CATEGORIES:
                await conn.execute(
                    "INSERT INTO categories (name_ru, name_en) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                    name_ru, name_en
                )

            for cat_name_ru, exercises in DEFAULT_EXERCISES.items():
                cat_row = await conn.fetchrow(
                    "SELECT id FROM categories WHERE name_ru = $1", cat_name_ru
                )
                if cat_row:
                    for exercise in exercises:
                        if isinstance(exercise, tuple):
                            name_ru, name_en = exercise
                        else:
                            name_ru = name_en = exercise
                        await conn.execute(
                            "INSERT INTO exercises (name_ru, name_en, category_id) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
                            name_ru, name_en, cat_row["id"]
                        )

            logger.info("Default data initialized")

    async def get_or_create_user(self, telegram_id: int, username: Optional[str] = None) -> int:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id FROM users WHERE telegram_id = $1", telegram_id
            )
            if row:
                return row["id"]

            row = await conn.fetchrow(
                "INSERT INTO users (telegram_id, username) VALUES ($1, $2) RETURNING id",
                telegram_id, username
            )
            await conn.execute(
                "INSERT INTO user_settings (user_id) VALUES ($1)", row["id"]
            )
            return row["id"]

    async def get_user_settings(self, user_id: int) -> Dict:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT language, units, notifications_enabled FROM user_settings WHERE user_id = $1",
                user_id
            )
            if not row:
                await conn.execute(
                    "INSERT INTO user_settings (user_id) VALUES ($1)", user_id
                )
                return {"language": "ru", "units": "metric", "notifications_enabled": False}
            return dict(row)

    async def update_user_settings(self, user_id: int, **kwargs) -> None:
        async with self._pool.acquire() as conn:
            sets = []
            values = []
            for i, (key, value) in enumerate(kwargs.items(), 1):
                sets.append(f"{key} = ${i}")
                values.append(value)
            values.append(user_id)
            await conn.execute(
                f"UPDATE user_settings SET {', '.join(sets)} WHERE user_id = ${len(values)}",
                *values
            )

    async def get_categories(self) -> List[Dict]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("SELECT id, name_ru, name_en FROM categories ORDER BY id")
            return [dict(r) for r in rows]

    async def add_category(self, name_ru: str, name_en: str = None) -> bool:
        name_en = name_en or name_ru
        async with self._pool.acquire() as conn:
            try:
                await conn.execute(
                    "INSERT INTO categories (name_ru, name_en) VALUES ($1, $2)",
                    name_ru, name_en
                )
                return True
            except asyncpg.UniqueViolationError:
                return False

    async def delete_category(self, name: str) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM categories WHERE name_ru = $1 OR name_en = $1", name
            )
            return "DELETE 1" in result

    async def get_exercises(self, category_id: int = None) -> List[Dict]:
        async with self._pool.acquire() as conn:
            if category_id:
                rows = await conn.fetch(
                    "SELECT id, name_ru, name_en FROM exercises WHERE category_id = $1 ORDER BY id",
                    category_id
                )
            else:
                rows = await conn.fetch("SELECT id, name_ru, name_en FROM exercises ORDER BY id")
            return [dict(r) for r in rows]

    async def add_exercise(self, name_ru: str, category_id: int, name_en: str = None) -> bool:
        name_en = name_en or name_ru
        async with self._pool.acquire() as conn:
            try:
                await conn.execute(
                    "INSERT INTO exercises (name_ru, name_en, category_id) VALUES ($1, $2, $3)",
                    name_ru, name_en, category_id
                )
                return True
            except asyncpg.UniqueViolationError:
                return False

    async def delete_exercise(self, name: str) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM exercises WHERE name_ru = $1 OR name_en = $1", name
            )
            return "DELETE 1" in result

    async def get_exercise_sets(self, exercise_id: int) -> List[Dict]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, name, sets, reps, weight FROM exercise_sets WHERE exercise_id = $1",
                exercise_id
            )
            return [dict(r) for r in rows]

    async def start_workout(self, user_id: int, category_name: str = None) -> int:
        async with self._pool.acquire() as conn:
            active = await conn.fetchrow(
                "SELECT id FROM workouts WHERE user_id = $1 AND is_active = TRUE", user_id
            )
            if active:
                return active["id"]

            row = await conn.fetchrow(
                "INSERT INTO workouts (user_id, category_name) VALUES ($1, $2) RETURNING id",
                user_id, category_name
            )
            return row["id"]

    async def get_active_workout(self, user_id: int) -> Optional[Dict]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, category_name, started_at FROM workouts WHERE user_id = $1 AND is_active = TRUE",
                user_id
            )
            return dict(row) if row else None

    async def add_workout_exercise(self, workout_id: int, exercise_name: str,
                                   sets: int, reps: int, weight: float = None) -> int:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "INSERT INTO workout_exercises (workout_id, exercise_name, sets, reps, weight) "
                "VALUES ($1, $2, $3, $4, $5) RETURNING id",
                workout_id, exercise_name, sets, reps, weight
            )
            await conn.execute(
                "UPDATE workouts SET total_exercises = total_exercises + 1 WHERE id = $1",
                workout_id
            )
            return row["id"]

    async def get_workout_exercises(self, workout_id: int) -> List[Dict]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT exercise_name, sets, reps, weight FROM workout_exercises "
                "WHERE workout_id = $1 ORDER BY created_at",
                workout_id
            )
            return [dict(r) for r in rows]

    async def finish_workout(self, workout_id: int) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE workouts SET is_active = FALSE, finished_at = CURRENT_TIMESTAMP WHERE id = $1",
                workout_id
            )

    async def cancel_workout(self, workout_id: int) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM workout_exercises WHERE workout_id = $1", workout_id
            )
            await conn.execute(
                "DELETE FROM workouts WHERE id = $1", workout_id
            )

    async def get_user_workouts(self, user_id: int, limit: int = 10, offset: int = 0) -> List[Dict]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, category_name, started_at, finished_at, total_exercises FROM workouts "
                "WHERE user_id = $1 AND is_active = FALSE ORDER BY started_at DESC LIMIT $2 OFFSET $3",
                user_id, limit, offset
            )
            return [dict(r) for r in rows]

    async def get_workout_by_id(self, workout_id: int) -> Optional[Dict]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, user_id, category_name, started_at, total_exercises FROM workouts WHERE id = $1",
                workout_id
            )
            return dict(row) if row else None

    async def get_workout_stats(self, user_id: int) -> Dict:
        async with self._pool.acquire() as conn:
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM workouts WHERE user_id = $1 AND is_active = FALSE", user_id
            )
            exercises = await conn.fetchval(
                "SELECT COALESCE(SUM(total_exercises), 0) FROM workouts WHERE user_id = $1", user_id
            )
            return {"total_workouts": total, "total_exercises": exercises}
