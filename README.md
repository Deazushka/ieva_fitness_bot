# Ieva Fitness Bot

Telegram-бот для отслеживания тренировок.

## Команды

| Команда | Описание |
|---------|----------|
| `/start` | Регистрация |
| `/help` | Справка |
| `/log <упражнение> <подходы>x<повторы> <вес>` | Записать тренировку |
| `/stats` | Статистика |
| `/history` | История |

**Примеры:**
- `/log bench press 3x10 60`
- `/log squat 5x5 100`
- `/log pull ups 3x12`

## Локальный запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Отредактируйте .env

uvicorn main:app --reload
```

## Деплой на Render

1. **Create Web Service** → подключите GitHub репозиторий
2. **Build Command:** `pip install -r requirements.txt`
3. **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. **Add PostgreSQL** (Free) — `DATABASE_URL` добавится автоматически
5. **Environment Variables:**
   - `TELEGRAM_BOT_TOKEN` — токен от @BotFather

## Технологии

- Python 3.12
- FastAPI + Uvicorn
- python-telegram-bot 21.0
- PostgreSQL (asyncpg)
