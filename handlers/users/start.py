from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import CommandStart
from utils.misc import db_commands as db

from data.config import ADMINS
from loader import dp
from states import Start


@dp.message_handler(CommandStart(deep_link='connect_user'), state='*')
async def connect_user(message: types.Message):
    if str(message.from_user.id) in ADMINS:
        return await db.verify_admin(message)

    await message.answer('Что бы получить доступ к боту, перейдите по инвайт ссылке '
                         'или введите код приглашения.')
    await Start.wait_id.set()


@dp.message_handler(CommandStart())
async def bot_start(message: types.Message):
    result = await db.select_user(message)

    if not result:
        if str(message.from_user.id) in ADMINS:
            return await db.verify_admin(message)

        if message.get_args() == '':
            await message.answer('Чтобы использовать этого бота введите код приглашения, '
                                 'либо пройдите по реферальной ссылке')
            await Start.wait_id.set()
            return

        await db.check_code(message, message.get_args())
    else:
        await message.answer(f"Привет, {message.from_user.full_name}!\n"
                             f"Ваш баланс: {result.balance}")


@dp.message_handler(state=Start.wait_id)
async def invite_code(message: types.Message, state: FSMContext):
    code = message.text
    if await db.check_code(message, code) is False:
        return
    await state.finish()
