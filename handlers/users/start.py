from random import randint
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import CommandStart
from sqlalchemy import update
from sqlalchemy.future import select

from loader import dp
from states import Start
from utils.db_api.db import async_session
from utils.db_api.models import Users


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
    await message.answer('Что бы получить доступ к боту, перейдите по инвайт ссылке '
                         'или введите код приглашения.')
    await Start.wait_id.set()


@dp.message_handler(CommandStart(), state='*')
async def bot_start(message: types.Message, state: FSMContext):
    print(type(message.from_user.id))
    async with async_session() as session:
        result = await session.execute(select(Users).where(Users.id == message.from_user.id))
        result = result.scalars().first()

        results_ = await session.execute(select(Users).where(Users.id == message.from_user.id))
        user = results_.scalars().first()

    if result is None:
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
                             f"Ваш баланс: {user.balance}")


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
