from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hide_link, hbold
from keyboards.inline.buy import show_item_button
from filters.authorized_users import AuthUser
from data.config import ADMINS
import utils.db_api.commands as db

from loader import dp


@dp.inline_handler(AuthUser(), state='*')
async def items_query(query: types.InlineQuery, state: FSMContext):
    starting_item = int(query.offset) if query.offset else 0

    results = await db.get_items(query.query, starting_item)

    items_list = []

    for item in results:
        id_for_admin = f'<b>id={item.item_id}\n</b>' \
            if await state.get_state() and str(query.from_user.id) in ADMINS else ''
        items_list.append(
            types.InlineQueryResultArticle(
                id=item.item_id,
                title=item.name,
                description=f'{item.price}₽\n{item.description}',
                thumb_url=item.thumb_url,
                input_message_content=types.InputTextMessageContent(
                    message_text=f'{hide_link(item.thumb_url)}{id_for_admin}'
                                 f'<b>Товар:</b> {item.name}\n'
                                 f'<b>Цена:</b> {item.price}₽\n'
                                 f'<b>Описание:</b>\n{item.description}\n\n'
                                 f'<i>Дата выставления товара: '
                                 f'{item.create_date.strftime("%d-%m-%Y %H:%M")}</i>'
                ),
                reply_markup=await show_item_button(item.item_id)
            )
        )

    await query.answer(
        results=items_list,
        cache_time=60,
        next_offset=str(starting_item+20)
    )
