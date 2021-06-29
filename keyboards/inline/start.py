from aiogram import types


start_inline = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [
            types.InlineKeyboardButton(
                text='Вперёд за покупками',
                switch_inline_query_current_chat=''
            )
        ]
    ]
)