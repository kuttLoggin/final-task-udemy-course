from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from data.config import ADMINS

class AdmM(BoundFilter):
    """Проверка на админа"""

    async def check(self, message: types.Message):
        if str(message.from_user.id) not in ADMINS:
            return False
        return True

class AdmC(BoundFilter):
    """Проверка на админа"""

    async def check(self, call: types.CallbackQuery):
        if str(call.from_user.id) not in ADMINS:
            return False
        return True
