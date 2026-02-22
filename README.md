# Ieva Fitness Bot

Telegram-бот для отслеживания тренировок с поддержкой PostgreSQL и webhook-режима.

## Команды

| Команда | Описание |
|---------|----------|
| `/start` | Регистрация в боте |
| `/help` | Справка по командам |
| `/log <упражнение> <подходы>x<повторы> <вес>` | Записать тренировку |
| `/stats` | Статистика тренировок |
| `/history` | История последних тренировок |

**Примеры:**
- `/log bench press 3x10 60` — жим лёжа, 3 подхода по 10 повторений, 60 кг
- `/log squat 5x5 100` — приседания, 5x5, 100 кг
- `/log pull ups 3x12` — подтягивания, 3x12

## Локальный запуск

```bash
# Клонировать репозиторий
git clone https://github.com/Deazushka/ieva_fitness_bot.git
cd ieva_fitness_bot

# Создать виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Создать .env файл
cp .env.example .env
# Добавить TELEGRAM_BOT_TOKEN и DATABASE_URL

# Запустить
python main.py
```

## Деплой на Render

### Требования

- Аккаунт на [Render](https://render.com)
- Аккаунт на GitHub
- Telegram Bot Token от [@BotFather](https://t.me/BotFather)

### Шаги

1. **Создать Web Service**
   - New → Web Service
   - Подключить репозиторий `ieva_fitness_bot`
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn main:app`

2. **Добавить PostgreSQL**
   - Add Resource → PostgreSQL (Free)
   - `DATABASE_URL` добавится автоматически

3. **Переменные окружения**
   - `TELEGRAM_BOT_TOKEN` — токен от BotFather

4. **Deploy** — Render автоматически запустит бота

### Автоматические переменные Render

| Переменная | Описание |
|------------|----------|
| `DATABASE_URL` | URL PostgreSQL (автоматически) |
| `RENDER_EXTERNAL_URL` | URL сервиса (автоматически) |

## Структура проекта

```
ieva_fitness_bot/
├── main.py              # Flask app + webhook endpoint
├── requirements.txt     # Зависимости Python
├── runtime.txt          # Версия Python (3.12)
├── Procfile             # Команда запуска для Render
├── src/
│   ├── bot.py           # Создание Application, setup webhook
│   ├── database.py      # PostgreSQL операции (asyncpg)
│   └── handlers.py      # Обработчики команд
├── tests/
│   └── test_bot.py      # Unit тесты
└── .env.example         # Пример переменных окружения
```

## Технологии

- **Python 3.12**
- **python-telegram-bot 21.0** — Telegram Bot API
- **asyncpg** — асинхронный PostgreSQL драйвер
- **Flask** — webhook endpoint
- **Gunicorn** — WSGI сервер
- **pytest** — тестирование

## Тестирование

```bash
source .venv/bin/activate
pytest tests/ -v
```
