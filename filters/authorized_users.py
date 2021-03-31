from sqlalchemy.future import select

from utils.db_api.db import async_session
from utils.db_api.models import Users

from aiogram import types
from aiogram.dispatcher.filters import BoundFilter


class AuthUserQ(BoundFilter):
    """Проверка на есть ли человек в бд или нет"""
    async def check(self, query: types.InlineQuery):
        user = query.from_user.id

        async with async_session() as session:
            result = await session.execute(select(Users).where(Users.id == user))
            result = result.scalars().first()

        if result is None:
            await query.answer(
                results=[],
                switch_pm_text='Вы неавторизированы Подключить бота',
                switch_pm_parameter='connect_user',
                cache_time=5
            )
            return False
        return True

class AuthUserM(BoundFilter):
    """Проверка на есть ли человек в бд или нет"""
    async def check(self, message: types.Message):
        user = message.from_user.id

        async with async_session() as session:
            result = await session.execute(select(Users).where(Users.id == user))
            result = result.scalars().first()

        if result is None:
            await message.answer('Что бы получить доступ к боту, перейдите по инвайт ссылке '
                                 'или введите код приглашения.')
            return False
        return True

