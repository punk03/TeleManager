"""
Конфигурационный файл для Telegram бота
"""
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Telegram API настройки
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID', 0))  # ID владельца бота

# Пути к файлам
PROFILES_FILE = 'config/profiles.json'
SESSION_NAME = 'profile_changer_session'

# Проверка наличия необходимых переменных окружения
if not all([API_ID, API_HASH, BOT_TOKEN, OWNER_ID]):
    raise ValueError("Пожалуйста, установите все необходимые переменные окружения в файле .env") 