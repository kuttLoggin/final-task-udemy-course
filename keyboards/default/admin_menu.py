from aiogram import types

admin_menu = types.ReplyKeyboardMarkup(
    keyboard=[
        [
            types.KeyboardButton(
                text='📦Управление товарами'
            )
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)
