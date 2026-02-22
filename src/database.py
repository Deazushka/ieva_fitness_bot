import asyncpg
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        if not self.database_url:
            raise ValueError('DATABASE_URL environment variable is required')

        self._pool = await asyncpg.create_pool(self.database_url, min_size=2, max_size=10)
        await self._create_tables()
        logger.info('Connected to PostgreSQL database')

    async def disconnect(self) -> None:
        if self._pool:
            await self._pool.close()
            logger.info('Disconnected from database')

    async def _create_tables(self) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS workouts (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    exercise TEXT NOT NULL,
                    sets INTEGER,
                    reps INTEGER,
                    weight REAL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS workout_plans (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
        logger.info('Database tables created/verified')

    async def get_or_create_user(self, telegram_id: int, username: Optional[str] = None) -> int:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT id FROM users WHERE telegram_id = $1', telegram_id
            )

            if row:
                return row['id']

            row = await conn.fetchrow(
                'INSERT INTO users (telegram_id, username) VALUES ($1, $2) RETURNING id',
                telegram_id, username
            )
            return row['id']

    async def add_workout(
        self,
        user_id: int,
        exercise: str,
        sets: Optional[int] = None,
        reps: Optional[int] = None,
        weight: Optional[float] = None,
        notes: Optional[str] = None
    ) -> int:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                '''INSERT INTO workouts (user_id, exercise, sets, reps, weight, notes)
                   VALUES ($1, $2, $3, $4, $5, $6) RETURNING id''',
                user_id, exercise, sets, reps, weight, notes
            )
            return row['id']

    async def get_user_workouts(self, user_id: int, limit: int = 10) -> list:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                '''SELECT exercise, sets, reps, weight, notes, created_at
                   FROM workouts WHERE user_id = $1
                   ORDER BY created_at DESC LIMIT $2''',
                user_id, limit
            )
            return [tuple(row.values()) for row in rows]

    async def get_workout_stats(self, user_id: int) -> dict:
        async with self._pool.acquire() as conn:
            total_row = await conn.fetchrow(
                'SELECT COUNT(*) as count FROM workouts WHERE user_id = $1', user_id
            )
            total_workouts = total_row['count']

            unique_row = await conn.fetchrow(
                'SELECT COUNT(DISTINCT exercise) as count FROM workouts WHERE user_id = $1',
                user_id
            )
            unique_exercises = unique_row['count']

            return {
                'total_workouts': total_workouts,
                'unique_exercises': unique_exercises
            }
