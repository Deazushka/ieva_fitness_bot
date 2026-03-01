# Telegram Fitness Bot 💪

Удобный и быстрый бот для отслеживания тренировок в Telegram.

## Требования
- Python 3.10+
- Токен Telegram бота от [@BotFather](https://t.me/BotFather)

---

## 🚀 Инструкция по развертыванию (Деплой на Render.com)

Render — это отличный облачный хостинг, который предоставляет бесплатный тариф для запуска веб-сервисов (подойдет для бота).

### Шаг 1: Подготовка
1. Убедитесь, что ваш код запушен в репозиторий на **GitHub**.
2. Получите `TELEGRAM_BOT_TOKEN` (токен бота) у @BotFather.

### Шаг 2: Создание Background Worker на Render
1. Зарегистрируйтесь на [Render.com](https://render.com/) через ваш GitHub аккаунт.
2. В панели управления (Dashboard) нажмите **New +** -> **Background Worker** (⚠️ важно выбрать именно этот тип, а не Web Service, так как бот работает в режиме polling и не требует открытого порта).
3. Выберите `Build and deploy from a Git repository`.
4. В списке репозиториев найдите `ieva_fitness_bot` (или вставьте ссылку на него) и нажмите **Connect**.

### Шаг 3: Настройка Background Worker
Заполните следующие поля:
- **Name:** Любое имя (например, `telegram-fitness-bot`).
- **Region:** Любой (рекомендуется Frankfurt, так он ближе к серверам Telegram).
- **Branch:** `main`
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt` (Команда сборки зависимостей)
- **Start Command:** `python main.py` (Команда запуска бота)
- **Instance Type:** `Free` (Бесплатный тариф)

### Шаг 4: Переменные окружения (ОЧЕНЬ ВАЖНО)
Прокрутите страницу вниз и нажмите на раздел **Advanced**.
Нажмите **Add Environment Variable** и добавьте токен вашего телеграм-бота:
- **Key:** `TELEGRAM_BOT_TOKEN`
- **Value:** `1234567890:AAaBbBcCcDdDeEeFfFgGhHiIjJkKlLmMnNo` (Ваш настоящий токен)

### Шаг 5: Запуск
Нажмите кнопку **Create Background Worker** в самом низу.
Render начнет собирать и запускать ваш код. Как только появится статус `In progress...` сменится на `Live`, можете открывать Telegram и проверять вашего бота — он уже будет работать 24/7 в облаке!

> **Важно про БД на бесплатном тарифе Render:** 
> Render очищает файлы на диске (Free Tier) при каждом перезапуске (Deploy/Спящий режим). Поэтому SQLite база данных `fitness_tracker.db` будет обнуляться каждый раз.
> Для постоянного хранения данных на Render необходимо подключить `Render Disk` (платная функция) либо переделать код на использование **PostgreSQL** базы данных (ее тоже можно создать бесплатно на Render).

---

## 🖥 Локальный запуск (Установка на свой компьютер)

Если нет `pip`, установите `Python` с официального сайта: python.org.

1. Откройте терминал/командную строку.
2. Создайте виртуальное окружение: `python3 -m venv venv` 
3. Активируйте:
   - macOS/Linux: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`
4. Установите библиотеки: `pip install -r requirements.txt`
5. Выполните:
   - macOS/Linux: `export TELEGRAM_BOT_TOKEN="Ваш_Токен" && python main.py`
   - Windows: `set TELEGRAM_BOT_TOKEN="Ваш_Токен" && python main.py`
