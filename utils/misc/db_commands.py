from loguru import logger

from loader import dp
from aiogram import types
from sqlalchemy import func
from sqlalchemy import update
from sqlalchemy.future import select
from utils.db_api.models import Users, Items
from utils.misc.hash_coded import encode
from utils.db_api.db import async_session


async def select_user_code(code):
    async with async_session() as session:
        result = await session.execute(select(Users).where(Users.code == code))
        return result.scalars().first()


async def select_user(user_id):
    async with async_session() as session:
        result = await session.execute(select(Users).where(Users.user_id == user_id))
        return result.scalars().first()


async def add_user(user):
    async with async_session() as session:
        async with session.begin():
            session.add(user)

async def update_user(text: dict, call):
    async with async_session() as session:
        stmt = update(Users).where(Users.user_id == call.from_user.id).values(text). \
            returning(Users.balance)
        await session.execute(stmt)
        await session.commit()


async def verify_admin(message):
    your_code = encode(message.from_user.id)
    admin = Users(user_id=message.from_user.id,
                  name=message.from_user.full_name,
                  balance=0,
                  code=your_code,
                  invited=None)
    await add_user(admin)

    bot = await dp.bot.me
    await message.answer(f'Здравствуйте, новый Администратор {message.from_user.full_name}\n'
                         f'Что бы открыть админ меню, пропишите /admin\n'
                         f'Ваш реферальный код <pre>{your_code}</pre>\n'
                         f'Или ссылка t.me/{bot.username}?start={your_code}')


async def check_code(message, code):
    result = select_user_code(code)

    if not result:
        return False, await message.answer('Неверный код приглашения')
    else:
        async with async_session() as session:
            stmt = update(Users).where(Users.code == code).values(balance=result.balance + 10). \
                returning(Users.code)

            your_code = encode(message.from_user.id)

            user_invited = Users(user_id=message.from_user.id,
                                 name=message.from_user.full_name,
                                 balance=0,
                                 code=your_code,
                                 invited=result.user_id)

            await session.execute(stmt)
            await session.commit()

        await add_user(user_invited)

        bot = await dp.bot.me
        await message.answer(f'Вы были приглашены пользователем <b>{result.name}</b>\n'
                             f'Вы можете получить бонус +10₽ если пригласите рефералов\n'
                             f'Ваш реферальный код <pre>{your_code}</pre>\n'
                             f'Или ссылка t.me/{bot.username}?start={your_code}',
                             reply_markup=types.InlineKeyboardMarkup(
                                 inline_keyboard=[
                                     [types.InlineKeyboardButton(
                                         text='Вперёд за покупками',
                                         switch_inline_query_current_chat=''
                                     )]
                                 ]
                             ))


async def select_item(item_id):
    async with async_session() as session:
        results = await session.execute(select(Items).where(Items.item_id == item_id))
        return results.scalars().first()


async def add_item(item):
    async with async_session() as session:
        async with session.begin():
            session.add(item)


def to_(self):
    d = {'name': self.name,
         'description': self.description,
         'price': self.price,
         'thumb_url': self.thumb_url,
         'pic': self.thumb_url}
    return d

async def update_item(data):
    old = data['old']
    for item in ['name', 'description', 'price', 'pic']:
        item_ = data[item]
        if item_ is None:
            continue

        async with async_session() as session:
            stmt = update(Items).where(Items.item_id == old.item_id).values({item: item_}). \
                returning(to_(Items)[item])

            await session.execute(stmt)
            await session.commit()
    return old

async def delete_item_FSM(data, call):
    item_id = data['item_id']
    logger.info(item_id)
    async with async_session() as session:
        results = await session.execute(select(Items).where(Items.item_id == int(item_id)))
        item = results.scalars().first()
        logger.info(item)

        if item is None:
            await call.message.edit_text('Товар не найден! :/')
            return False

        await session.delete(item)
        await session.commit()
        return item_id
