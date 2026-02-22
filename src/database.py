import aiosqlite
import logging
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv('DATABASE_PATH', 'workout.db')
        self._connection: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        self._connection = await aiosqlite.connect(self.db_path)
        await self._create_tables()
        logger.info(f'Connected to database: {self.db_path}')

    async def disconnect(self) -> None:
        if self._connection:
            await self._connection.close()
            logger.info('Disconnected from database')

    async def _create_tables(self) -> None:
        await self._connection.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS workouts (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                exercise TEXT NOT NULL,
                sets INTEGER,
                reps INTEGER,
                weight REAL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );

            CREATE TABLE IF NOT EXISTS workout_plans (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        ''')
        await self._connection.commit()

    async def get_or_create_user(self, telegram_id: int, username: Optional[str] = None) -> int:
        cursor = await self._connection.execute(
            'SELECT id FROM users WHERE telegram_id = ?', (telegram_id,)
        )
        row = await cursor.fetchone()
        
        if row:
            return row[0]
        
        cursor = await self._connection.execute(
            'INSERT INTO users (telegram_id, username) VALUES (?, ?)',
            (telegram_id, username)
        )
        await self._connection.commit()
        return cursor.lastrowid

    async def add_workout(
        self,
        user_id: int,
        exercise: str,
        sets: Optional[int] = None,
        reps: Optional[int] = None,
        weight: Optional[float] = None,
        notes: Optional[str] = None
    ) -> int:
        cursor = await self._connection.execute(
            '''INSERT INTO workouts (user_id, exercise, sets, reps, weight, notes)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (user_id, exercise, sets, reps, weight, notes)
        )
        await self._connection.commit()
        return cursor.lastrowid

    async def get_user_workouts(self, user_id: int, limit: int = 10) -> list:
        cursor = await self._connection.execute(
            '''SELECT exercise, sets, reps, weight, notes, created_at
               FROM workouts WHERE user_id = ?
               ORDER BY created_at DESC LIMIT ?''',
            (user_id, limit)
        )
        return await cursor.fetchall()

    async def get_workout_stats(self, user_id: int) -> dict:
        cursor = await self._connection.execute(
            'SELECT COUNT(*) FROM workouts WHERE user_id = ?', (user_id,)
        )
        total_workouts = (await cursor.fetchone())[0]

        cursor = await self._connection.execute(
            'SELECT COUNT(DISTINCT exercise) FROM workouts WHERE user_id = ?',
            (user_id,)
        )
        unique_exercises = (await cursor.fetchone())[0]

        return {
            'total_workouts': total_workouts,
            'unique_exercises': unique_exercises
        }
