from loguru import logger
from aiogram import executor
import asyncpg

# Бот:
from loader import dp
import middlewares, filters, handlers

# Бд:
from utils.db_api.db import engine
from utils.db_api.models import Base

# Прочие:
from utils.notify_admins import on_startup_notify

async def on_startup(dispatcher):
    logger.info('Подключаем бд')
    async with engine.begin() as conn:
        # Создаем таблицы если их нету
        await conn.run_sync(Base.metadata.create_all)

    logger.info('Уведомляем Администрацию')
    await on_startup_notify(dispatcher)
    logger.info('Бот запущен')


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
