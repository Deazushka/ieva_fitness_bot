# 🏋️ Telegram Fitness Tracker Bot

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-20.7-green.svg)](https://github.com/python-telegram-bot/python-telegram-bot)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Умный Telegram-бот для отслеживания тренировок с FSM, inline кнопками и историей.

## ✨ Возможности

- 🎯 **Управление тренировками**
  - Начать/завершить тренировку
  - Выбор категории (ноги, руки, спина, грудь и т.д.)
  - Добавление/удаление категорий и упражнений
  - Ввод подходов, повторений и веса

- 📊 **История и статистика**
  - Просмотр истории тренировок
  - Детализация каждой тренировки
  - Статистика по упражнениям

- ⚙️ **Настройки**
  - Выбор языка (RU/EN)
  - Единицы измерения (метрические/имперские)
  - Настройка уведомлений

- 🎨 **Современный UI**
  - Inline кнопки для удобной навигации
  - FSM для управления состояниями
  - Интуитивный интерфейс

## 📸 Интерфейс

```
┌─────────────────────────────────┐
│ 🏋️ Главное меню                 │
├─────────────────────────────────┤
│ [🏋️ Начать тренировку]         │
│ [📊 История]  [⚙️ Настройки]    │
│ [❓ Помощь]                     │
└─────────────────────────────────┘
```

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.9 или выше
- Telegram аккаунт
- Токен от @BotFather

### Установка

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/your-username/tranie_bot.git
cd tranie_bot
```

2. **Создайте виртуальное окружение (рекомендуется):**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

4. **Настройте переменные окружения:**
```bash
cp .env.example .env
```

Отредактируйте `.env`:
```bash
TELEGRAM_BOT_TOKEN=your_token_here
LOG_LEVEL=INFO
```

5. **Получите токен бота:**
   - Откройте Telegram
   - Найдите `@BotFather`
   - Отправьте `/newbot`
   - Следуйте инструкциям
   - Скопируйте полученный токен в `.env`

6. **Запустите бота:**
```bash
python bot.py
```

### Проверка работы

Откройте Telegram, найдите вашего бота и отправьте `/start`.

## 📖 Использование

### Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Начать работу с ботом |
| `/help` | Показать справку |
| `/history` | История тренировок |
| `/settings` | Настройки пользователя |
| `/cancel` | Отменить текущее действие |

### Начало тренировки

1. Отправьте `/start`
2. Нажмите "🏋️ Начать тренировку"
3. Выберите категорию (день ног, день рук и т.д.)
4. Выберите упражнение из списка
5. Введите подходы и повторения:
   - `3x12` — 3 подхода по 12 повторений
   - `4x10,50` — 4 подхода по 10 повторений с весом 50 кг
   - `5x5x100` — 5x5 с весом 100 кг
6. Добавьте другие упражнения
7. Нажмите "✅ Завершить тренировку"

### Просмотр истории

1. Нажмите "📊 История"
2. Используйте пагинацию для навигации
3. Нажмите на тренировку для детализации

### Настройки

- **Язык**: Русский / English
- **Единицы**: Метрические (кг) / Имперские (фунты)
- **Уведомления**: Вкл/Выкл

## 🏗️ Архитектура

### Диаграмма состояний FSM

```
┌─────────────┐
│  MAIN_MENU  │
└──────┬──────┘
       │
       ├──[Начать тренировку]──→ CATEGORY_SELECT
       │                              │
       │                              ├──[Выбор категории]──→ EXERCISE_SELECT
       │                              │                            │
       │                              │                            ├──[Выбор упражнения]──→ EXERCISE_INPUT
       │                              │                            │                              │
       │                              │                            │                              └──[Ввод данных]──┐
       │                              │                            │                                                   │
       │                              │                            └──[Завершить]──→ MAIN_MENU ←────────────────────┘
       │                              │
       │                              └──[Назад]──→ MAIN_MENU
       │
       ├──[История]──→ HISTORY_MENU
       │                     │
       │                     └──[Назад]──→ MAIN_MENU
       │
       └──[Настройки]──→ SETTINGS_MENU
                              │
                              └──[Назад]──→ MAIN_MENU
```

### Структура базы данных

```sql
categories
├── id (PK)
├── name (UNIQUE)
└── created_at

exercises
├── id (PK)
├── name (UNIQUE)
├── category_id (FK → categories.id)
└── created_at

workouts
├── id (PK)
├── user_id
├── username
├── category_name
├── started_at
├── finished_at
├── total_exercises
└── notes

workout_exercises
├── id (PK)
├── workout_id (FK → workouts.id)
├── exercise_name
├── sets
├── reps
├── weight
├── notes
└── created_at

user_settings
├── user_id (PK)
├── language
├── units
├── notifications_enabled
├── notification_time
├── created_at
└── updated_at
```

## 📁 Структура проекта

```
tranie_bot/
├── bot.py              # Основной файл бота с FSM
├── database.py         # Модуль работы с SQLite
├── config.py           # Конфигурация и переменные окружения
├── constants.py        # Константы и локализация
├── requirements.txt    # Зависимости Python
├── .env.example        # Шаблон переменных окружения
├── .gitignore          # Исключения Git
├── README.md           # Этот файл
├── CHANGELOG.md        # История изменений
├── CONTRIBUTING.md     # Руководство для контрибьюторов
├── LICENSE             # Лицензия MIT
└── workout.db         # База данных (создается автоматически)
```

## 🔧 Разработка

### Запуск в режиме разработки

```bash
# Установите LOG_LEVEL=DEBUG в .env
LOG_LEVEL=DEBUG

python bot.py
```

### Линтинг и форматирование

```bash
pip install black flake8
black *.py
flake8 *.py
```

## ☁️ Деплой

### Render.com (бесплатно)

1. Создайте Web Service на [Render.com](https://render.com/)
2. Подключите GitHub репозиторий
3. Настройте:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python bot.py`
4. Добавьте переменную окружения `TELEGRAM_BOT_TOKEN`

### Railway.app

1. Создайте проект на [Railway](https://railway.app/)
2. Подключите репозиторий
3. Добавьте `TELEGRAM_BOT_TOKEN` в переменные окружения

### Docker (опционально)

Создайте `Dockerfile`:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

Запуск:
```bash
docker build -t fitness-bot .
docker run -d -e TELEGRAM_BOT_TOKEN=your_token fitness-bot
```

## 🐛 Устранение проблем

### Бот не запускается

- ✅ Проверьте Python версию: `python --version` (должен быть 3.9+)
- ✅ Убедитесь, что установлен токен в `.env`
- ✅ Проверьте зависимости: `pip install -r requirements.txt`
- ✅ Посмотрите логи на ошибки

### Ошибка "TELEGRAM_BOT_TOKEN not found"

- ✅ Создайте файл `.env` из `.env.example`
- ✅ Вставьте ваш токен
- ✅ Убедитесь, что `.env` в той же папке, что и `bot.py`

### Бот не отвечает на сообщения

- ✅ Проверьте, что бот запущен
- ✅ Убедитесь, что вы используете inline кнопки
- ✅ Отправьте `/start` для сброса состояния

### Ошибки базы данных

- ✅ Удалите файл `workout.db` и перезапустите бота
- ✅ Проверьте права доступа к файлу

## 🗺️ Roadmap

### v1.1 (Следующий релиз)
- [ ] Графики прогресса (matplotlib)
- [ ] Экспорт в CSV
- [ ] Напоминания о тренировках

### v1.2
- [ ] Web-интерфейс (Flask/Django)
- [ ] REST API
- [ ] Мультиязычность (ES, DE, FR)

## 🤝 Вклад в проект

Мы приветствуем любой вклад! См. [CONTRIBUTING.md](CONTRIBUTING.md) для руководства.

## 📝 Changelog

См. [CHANGELOG.md](CHANGELOG.md) для истории изменений.

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. [LICENSE](LICENSE) файл.

---

**Сделано с ❤️ для фитнес-сообщества**
# ieva_fitnes_bot
