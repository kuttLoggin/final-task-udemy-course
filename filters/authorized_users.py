from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.filters import BoundFilter
from utils.db_api.commands import get_user


class AuthUser(BoundFilter):
    """Проверка на есть ли человек в базе данных"""
    async def check(self, obj: types.Update):
        if isinstance(obj, types.Message):
            msg: types.Message = obj
        elif isinstance(obj, types.InlineQuery):
            msg: types.InlineQuery = obj
        else:
            raise CancelHandler()

        if not await get_user(msg.from_user.id):
            if isinstance(obj, types.Message):
                await msg.answer('Что бы получить доступ к боту, перейдите по инвайт ссылке '
                                 'или введите код приглашения.')
            else:
                await msg.answer(
                    results=[],
                    switch_pm_text='Вы не авторизированны Подключить бота',
                    switch_pm_parameter='',
                    cache_time=5
                )
            raise CancelHandler()
        return True

