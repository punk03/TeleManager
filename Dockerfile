FROM python:3.8-slim

# Установка рабочей директории
WORKDIR /app

# Копирование файлов проекта
COPY requirements.txt .
COPY telegram_profile_bot.py .
COPY profiles.json .
COPY .env.example .env
COPY config/ ./config/

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Создание volume для хранения сессий и профилей
VOLUME ["/app/sessions", "/app/config"]

# Запуск бота
CMD ["python", "telegram_profile_bot.py"] 