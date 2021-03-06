import re
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, Command
from aiogram.utils.markdown import hide_link, quote_html

from filters.admin import Admin
from keyboards.default.admin_menu import admin_menu
from keyboards.inline.admin_act import (admin_items_act, items_act, button_cancel,
                                        button_confirm_add, change_item,
                                        item_change, change_item_v1, button_confirm_del)
from states.admin import ItemsAct
from loader import dp

from utils.db_api.models import Items
import utils.db_api.commands as db


async def get_info_fsm(data):
    info = ['name', 'description', 'price', 'pic']
    act = {'name': '<b>Название</b>', 'description': '<b>Описание</b>',
           'price': '<b>Стоимостью</b>', 'pic': '<b>Ссылку для фото</b>'}
    old_and_now = []

    for key in info:
        if data[key] is not None:
            old_and_now.append(f'{act[key]}: <s>{db.to_(data["old"])[key]}</s> {data[key]}\n')
    return '\n'.join(old_and_now)


@dp.message_handler(Admin(), Command('admin', '/!', ignore_case=True))
async def show_menu(message: types.Message):
    await message.answer('Открываю вам меню\n', reply_markup=admin_menu)


@dp.message_handler(Admin(), Text(contains='Управление товарами', ignore_case=True))
async def control_items(message: types.Message):
    await message.answer('Управление товарами', reply_markup=admin_items_act)


@dp.callback_query_handler(Admin(), items_act.filter(act='add'))
async def add_items(call: types.CallbackQuery):
    await call.message.edit_text('Введите данные о товаре что бы внести его в список\n'
                                 'Ввести надо <b>Название товара, цена (обязательно с точкой), '
                                 'описание (не обязательно), ссылку на фото</b> через строчку\n\n'
                                 'Пример:\n'
                                 'Ананас\n'
                                 '60\n'
                                 'Самый вкусный\n'
                                 'https://images.av.ru/av.ru/product/h53/h1b/8953463635998.jpg',
                                 disable_web_page_preview=True,
                                 reply_markup=button_cancel)
    await ItemsAct.add_wait_text.set()


@dp.message_handler(Admin(), state=ItemsAct.add_wait_text)
async def add_item(message: types.Message, state: FSMContext):
    try:
        name, price, description, pic = message.text.split('\n')
    except ValueError:
        await message.answer('Текст заполнен не правильно')
    else:
        await message.answer('%s'
                             '<b>Товар:</b> %s\n'
                             '<b>Цена:</b> %s₽\n'
                             '<b>Описание:</b>\n%s\n\n'
                             '<i>Дата выставления товара: сейчас</i>' % \
                             (hide_link(pic), name, price, description))
        await state.update_data(name=name, price=price, description=description, pic=pic)
        await message.answer('Вы уверены что хотите добавить этот товар?',
                             reply_markup=button_confirm_add)


@dp.callback_query_handler(Admin(), text='confirm_add', state=ItemsAct.add_wait_text)
async def confirm_add(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    try:
        item = Items(name=data['name'], price=int(data['price']),
                     description=data['description'], thumb_url=data['pic'])
        await db.add_item(item)
    except Exception as err:
        await call.message.edit_text(f'Что-то пошло не так и товар не был добавлен!\n'
                                     f'{quote_html(err)}', reply_markup=None)
    else:
        await call.message.edit_text('Товар успешно добавлен!', reply_markup=None)
    await state.finish()


@dp.callback_query_handler(Admin(), items_act.filter(act='change'))
async def change_items(call: types.CallbackQuery):
    await call.message.edit_text('Пришлите мне через инлайн мод товар который вы хотите изменить',
                                 reply_markup=button_cancel)
    await ItemsAct.change_wait_item.set()


@dp.message_handler(Admin(), state=ItemsAct.change_wait_item)
async def wait_msg(message: types.Message, state: FSMContext):
    data = await state.get_data()
    for class_name in ['name', 'description', 'price', 'pic']:
        if class_name in data:
            item_info = await get_info_fsm(data)
            await message.answer(f'{item_info}\n'
                                 f'Что вы хотите изменить у этого товара?',
                                 reply_markup=change_item_v1, disable_web_page_preview=True)
            return

    if message.via_bot.id != (await dp.bot.me).id:
        await message.answer('Пришлите сообщение через инлайн мод этого бота.')
        return

    item_id = re.compile(r'id=(\d+)')

    try:
        item_id = int(item_id.match(message.text, pos=1).group(1))
    except (AttributeError, ValueError):
        await message.answer('Что-то пошло не так, попробуйте ещё раз.')
        return

    item = await db.get_item(item_id)

    if not item:
        await message.answer('Товар не найден! :/')
        return

    await message.answer('Что вы хотите изменить у этого товара?', reply_markup=change_item)
    await state.update_data(item_id=item_id, old=item, name=None,
                            description=None, price=None, pic=None)


@dp.callback_query_handler(Admin(), item_change.filter(act='save'), state=ItemsAct.change_wait_item)
async def save(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    item = await db.update_item(data)

    await call.message.edit_text(f'Товар №{item.item_id} обновлён', reply_markup=None)
    await state.finish()


@dp.callback_query_handler(Admin(), item_change.filter(), state=ItemsAct.change_wait_item)
async def item_change_all(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    act = callback_data.get('act')
    acts = {'name': 'е <b>Название</b>', 'description': 'е <b>Описание</b>',
            'price': 'ю <b>Стоимость</b>', 'pic': 'ю <b>Фото</b>'}
    await call.message.edit_text(f'Отправьте ново{acts[act]}', reply_markup=None)
    await state.update_data(act=act)
    await ItemsAct.change_wait_input.set()


@dp.message_handler(Admin(), state=ItemsAct.change_wait_input)
async def change_item_(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if data['act'] == 'name':
        if len(message.text) > 255:
            await message.answer('Такое название товара слишком длинное, надо меньше')
            return
    elif data['act'] == 'description':
        if len(message.text) > 1024:
            await message.answer('Такое описания для товара слишком длинное, надо меньше')
            return
    elif data['act'] == 'price':
        try:
            int(message.text)
        except ValueError:
            await message.answer('Стоимоть товара должна быть в цифрах!')
            return
        message.text = int(message.text)
    elif data['act'] == 'pic':
        if message.text[0:8] == 'https://' or message.text[0:7] == 'http://':
            pass
        else:
            await message.answer('Ссылка неправильная!')
            return
    await state.update_data({data['act']: message.text})
    await ItemsAct.change_wait_item.set()
    await wait_msg(message, state)


@dp.callback_query_handler(Admin(), items_act.filter(act='del'))
async def del_item(call: types.CallbackQuery):
    await call.message.edit_text('Пришлите мне через инлайн мод товар который вы хотите удалить',
                                 reply_markup=button_cancel)
    await ItemsAct.del_wait_item.set()


@dp.message_handler(Admin(), state=ItemsAct.del_wait_item)
async def wait_del_item(message: types.Message, state: FSMContext):
    if message.via_bot.id != (await dp.bot.me).id:
        await message.answer('Пришлите сообщение через инлайн мод этого бота.')
        return

    item_id = re.compile(r'id=(\d+)')
    try:
        item_id = item_id.match(message.text, pos=1).group(1)
        item_id = int(item_id)
    except (AttributeError, ValueError):
        await message.answer('Что-то пошло не так, попробуйте ещё раз.')

    await state.update_data(item_id=item_id)
    await message.answer('Вы уверены что хотите <b>удалить этот товар</b>?',
                         reply_markup=button_confirm_del)


@dp.callback_query_handler(Admin(), text='confirm_del', state=ItemsAct.del_wait_item)
async def delete_item(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    item_id = await db.delete_item(data, call)
    if item_id is False:
        return

    await call.message.edit_text(f'Товар №{item_id} удалён!', reply_markup=None)
    await state.finish()


@dp.callback_query_handler(Admin(), text='cancel', state='*')
async def cancel_callback(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_text('Вы отменили', reply_markup=None)
    await state.finish()


@dp.message_handler(Admin(), Command('cancel', '/!', ignore_case=True), state='*')
async def cancel_message(message: types.Message, state: FSMContext):
    await message.edit_text('Вы отменили', reply_markup=None)
    await state.finish()
