from aiogram import types
from aiogram.utils.callback_data import CallbackData

items_act = CallbackData('items_act', 'act')
item_change = CallbackData('item_change', 'act')


admin_items_act = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [
            types.InlineKeyboardButton(
                text='Добавить',
                callback_data=items_act.new(act='add')
            ),
            types.InlineKeyboardButton(
                text='Изменить',
                callback_data=items_act.new(act='change')
            ),
            types.InlineKeyboardButton(
                text='Удалить',
                callback_data=items_act.new(act='del')
            )
        ]
    ]
)

change_item = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [
            types.InlineKeyboardButton(
                text='✏Название',
                callback_data=item_change.new(act='name')
            ),
            types.InlineKeyboardButton(
                text='⌨Описание',
                callback_data=item_change.new(act='description')
            )
        ],
        [
            types.InlineKeyboardButton(
                text='💵Стоимость',
                callback_data=item_change.new(act='price')
            ),
            types.InlineKeyboardButton(
                text='🖼Фото',
                callback_data=item_change.new(act='thumb_url')
            )
        ],
        [
            types.InlineKeyboardButton(
                text='Отменить',
                callback_data='cancel'
            )
        ]
    ]
)


change_item_v1 = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [
            types.InlineKeyboardButton(
                text='✏Название',
                callback_data=item_change.new(act='name')
            ),
            types.InlineKeyboardButton(
                text='⌨Описание',
                callback_data=item_change.new(act='description')
            )
        ],
        [
            types.InlineKeyboardButton(
                text='💵Стоимость',
                callback_data=item_change.new(act='price')
            ),
            types.InlineKeyboardButton(
                text='🖼Фото',
                callback_data=item_change.new(act='thumb_url')
            )
        ],
        [
            types.InlineKeyboardButton(
                text='✅Сохранить',
                callback_data=item_change.new(act='save')
            ),
            types.InlineKeyboardButton(
                text='❌Отменить',
                callback_data='cancel'
            ),
        ]
    ]
)


button_cancel = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [
            types.InlineKeyboardButton(
                text='Отмена',
                callback_data='cancel'
            )
        ]
    ]
)

button_confirm_add = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [
            types.InlineKeyboardButton(
                text='Подтверить',
                callback_data='confirm_add'
            ),
            types.InlineKeyboardButton(
                text='Отмена',
                callback_data='cancel'
            )
        ]
    ]
)

button_confirm_del = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [
            types.InlineKeyboardButton(
                text='Подтверить',
                callback_data='confirm_del'
            ),
            types.InlineKeyboardButton(
                text='Отмена',
                callback_data='cancel'
            )
        ]
    ]
)
