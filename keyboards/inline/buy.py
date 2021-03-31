from aiogram import types
from aiogram.utils.callback_data import CallbackData

buy_item = CallbackData('buy_item', 'id')


def buy_button(item_id: int):
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text='Купить',
                    callback_data=buy_item.new(id=item_id)
                )
            ]
        ]
    )

def show_item_button(item, username):
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text='Показать товар',
                    url=f't.me/{username}?start=item_id-{str(item.id)}'
                )
            ]
        ]
    )
