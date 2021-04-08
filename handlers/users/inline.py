from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hide_link
from loguru import logger
from sqlalchemy import func
from sqlalchemy.future import select

from data.config import ADMINS
from filters.authorized_users import AuthUserQ
from keyboards.inline.buy import show_item_button
from loader import dp

from utils.db_api.db import async_session
from utils.db_api.models import Items


async def id_item(state, query, id):
    if query.from_user.id not in ADMINS:
        if await state.get_state() is not None:
            return f"<b>id={id}</b>\n"
        return ''
    return ''


@dp.inline_handler(AuthUserQ(), text='', state='*')
async def empty_query(query: types.InlineQuery, state: FSMContext):
    starting_item = int(query.offset) if query.offset else 0

    async with async_session() as session:
        results = await session.execute(select(Items).order_by(Items.name).offset(starting_item).limit(20))
        result = results.scalars()

    items_list = []

    for item in result:
        items_list.append(
            types.InlineQueryResultArticle(
                id=item.item_id,
                title=item.name,
                description='%s₽\n%s' % (item.price, item.description),
                thumb_url=item.thumb_url,
                input_message_content=types.InputTextMessageContent(
                    message_text=f'%s{await id_item(state, query, item.item_id)}'
                                 f'<b>Товар:</b> %s\n'
                                 f'<b>Цена:</b> %s₽\n'
                                 f'<b>Описание:</b>\n%s\n\n'
                                 f'<i>Дата выставления товара: %s</i>' % \
                                 (hide_link(item.thumb_url), item.name, item.price, item.description, item.create_date.strftime('%d-%m-%Y %H:%M'))
                ),
                reply_markup=show_item_button(item, (await dp.bot.me).username)
            )
        )

    await query.answer(
        results=items_list,
        cache_time=5,
        next_offset=str(starting_item+20)
    )


@dp.inline_handler(AuthUserQ(), state='*')
async def items_query(query: types.InlineQuery, state: FSMContext):
    starting_item = int(query.offset) if query.offset else 0

    text = query.query.lower()
    async with async_session() as session:
        results = await session.execute(select(Items).filter(func.lower(Items.name).\
                                                             like(f'%{text}%')).order_by(Items.name).offset(starting_item).limit(20))
        result = results.scalars()

    list_items = []
    for item in result:
        list_items.append(
            types.InlineQueryResultArticle(
                id=item.item_id,
                title=item.name,
                description='%s₽\n%s' % (item.price, item.description),
                thumb_url=item.thumb_url,
                input_message_content=types.InputTextMessageContent(
                    message_text=f'%s{await id_item(state, query, item.item_id)}'
                                 f'<b>Товар:</b> %s\n'
                                 f'<b>Цена:</b> %s₽\n'
                                 f'<b>Описание:</b>\n%s\n\n'
                                 f'<i>Дата выставления товара: %s</i>' % \
                                 (hide_link(item.thumb_url), item.name, item.price, item.description, item.create_date.strftime('%d-%m-%Y %H:%M %Z'))
                ),
                reply_markup=show_item_button(item, (await dp.bot.me).username)
            )
        )

    await query.answer(
        results=list_items,
        cache_time=2,
        next_offset=str(starting_item+20)
    )
