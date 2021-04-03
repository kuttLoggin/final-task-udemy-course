from random import randint
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import CommandStart
from sqlalchemy import update
from sqlalchemy.future import select

from data.config import ADMINS
from loader import dp
from states import Start
from utils.db_api.db import async_session
from utils.db_api.models import Users

from loguru import logger

async def check_code(message, code):
    async with async_session() as session:
        result = await session.execute(select(Users).where(Users.code == code))
        result = result.scalars().first()
    if result is None:
        await message.answer('Неверный код приглашения')
        return False
    else:
        async with async_session() as session:
            while True:
                your_code = randint(1, 257892246898)
                result_invited = await session.execute(select(Users).where(Users.code == your_code))
                result_invited = result_invited.scalars().first()
                if result_invited is None:
                    break

            stmt = update(Users).where(Users.code == code).values(balance=float(result.balance) + 10.00). \
                returning(Users.code)

            user_invited = Users(id=message.from_user.id,
                                 name=message.from_user.full_name,
                                 balance=0.00,
                                 code=your_code,
                                 invited=result.id)

            await session.execute(stmt)
            await session.commit()

        async with session.begin():
            session.add(user_invited)

        bot_user = await dp.bot.me
        await message.answer(f'Вы были приглашены пользователем <b>{result.name}</b>\n'
                             f'Вы можете получить бонус +10₽ если пригласите рефералов\n'
                             f'Ваш реферальный код <pre>{your_code}</pre>\n'
                             f'Или ссылка t.me/{bot_user.username}?start={your_code}',
                             reply_markup=types.InlineKeyboardMarkup(
                                 inline_keyboard=[
                                     [types.InlineKeyboardButton(
                                         text='Вперёд за покупками',
                                         switch_inline_query_current_chat=''
                                     )]
                                 ]
                             ))


@dp.message_handler(CommandStart(deep_link='connect_user'), state='*')
async def connect_user(message: types.Message):
    if str(message.from_user.id) in ADMINS:
        your_code = randint(1, 257892246898)
        admin = Users(id=message.from_user.id,
                      name=message.from_user.full_name,
                      balance=0.00,
                      code=your_code,
                      invited=None)
        async with async_session() as session:
            async with session.begin():
                session.add(admin)

        await message.answer(f'Здравствуйте, новый Администратор {message.from_user.full_name}')

        return
    await message.answer('Что бы получить доступ к боту, перейдите по инвайт ссылке '
                         'или введите код приглашения.')
    await Start.wait_id.set()


@dp.message_handler(CommandStart())
async def bot_start(message: types.Message, state: FSMContext):
    async with async_session() as session:
        result = await session.execute(select(Users).where(Users.id == message.from_user.id))
        result = result.scalars().first()

    if result is None:
        if str(message.from_user.id) in ADMINS:
            your_code = randint(1, 257892246898)
            admin = Users(id=message.from_user.id,
                          name=message.from_user.full_name,
                          balance=0.00,
                          code=your_code,
                          invited=None)
            async with session.begin():
                session.add(admin)

            await message.answer(f'Здравствуйте, новый Администратор {message.from_user.full_name}')

            return
        if message.get_args() == '':
            await message.answer('Чтобы использовать этого бота введите код приглашения, '
                                 'либо пройдите по реферальной ссылке')
            await Start.wait_id.set()
        else:
            if len(message.get_args()) > 12:
                await message.answer('Неверный код приглашения')
                return
            try:
                code = int(message.get_args())
            except ValueError:
                await message.answer('Неверный код приглашения')
            else:
                await check_code(message, code)
    else:
        await message.answer(f"Привет, {message.from_user.full_name}!\n"
                             f"Ваш баланс: {result.balance}")


@dp.message_handler(state=Start.wait_id)
async def invite_code(message: types.Message, state: FSMContext):
    if len(message.text) > 12:
        await message.answer('Неверный код приглашения')
        return
    try:
        code = int(message.text)
    except ValueError:
        await message.answer('Введите код приглашения')
    else:
        if await check_code(message, code) is False:
            return
        await state.finish()
