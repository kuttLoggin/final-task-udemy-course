from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from aiogram.dispatcher.handler import CancelHandler

from data.config import ADMINS


class Admin(BoundFilter):
    """Проверка на админа"""

    async def check(self, obj: types.Update) -> bool:
        if isinstance(obj, types.Message):
            msg: types.Message = obj
        elif isinstance(obj, types.CallbackQuery):
            msg: types.CallbackQuery = obj
        else:
            raise CancelHandler()
        return str(msg.from_user.id) in ADMINS
