from aiogram import types
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.deep_linking import get_start_link


buy_item = CallbackData('buy_item', 'id')


def buy_button(item_id: int):
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text='Оплатить',
                    callback_data=buy_item.new(id=item_id)
                )
            ]
        ]
    )

async def show_item_button(item_id: int):
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text='Показать товар',
                    url=await get_start_link(f'item_id-{item_id}')
                )
            ]
        ]
    )


req_location = types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(
                    text='Отправить свою геолокацию',
                    request_location=True
                )
            ]
        ],
        one_time_keyboard=True,
        resize_keyboard=True
    )
