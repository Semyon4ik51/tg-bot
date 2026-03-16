import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

if BOT_TOKEN is None:
    raise Exception("Токен не найден! Проверь файл .env")