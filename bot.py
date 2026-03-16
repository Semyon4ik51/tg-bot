import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN
from handlers import router
from scheduled import daily_notification
from init_db import init_schedule   # <-- добавили импорт

logging.basicConfig(level=logging.INFO)

async def main():
    # Инициализация базы данных (заполнение расписания, если пусто)
    init_schedule()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    # Удаляем вебхук, если он был установлен ранее
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.sleep(1)  # небольшая задержка для гарантии

    scheduler = AsyncIOScheduler()
    scheduler.add_job(daily_notification, 'cron', hour=16, minute=0, args=[bot])
    scheduler.start()

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
