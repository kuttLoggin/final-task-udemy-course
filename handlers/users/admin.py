from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, Command
from aiogram.utils.markdown import hide_link
import re

from sqlalchemy import update
from sqlalchemy.future import select

from filters.admin import AdmM, AdmC
from keyboards.default.admin_menu import admin_menu
from keyboards.inline.admin_act import admin_items_act, items_act, button_cancel, button_confirm_add, change_item, \
    item_change, change_item_v1, button_confirm_del
from states.admin import ItemsAct
from loader import dp

from utils.db_api.db import async_session
from utils.db_api.models import Items


@dp.message_handler(AdmM(), Text(contains='Админ', ignore_case=True))
@dp.message_handler(AdmM(), Text(contains='Admin'))
async def show_menu(message: types.Message):
    await message.answer('Открываю вам меню', reply_markup=admin_menu)


@dp.message_handler(AdmM(), Text(contains='Управление товарами', ignore_case=True))
async def control_items(message: types.Message):
    await message.answer('Управление товарами', reply_markup=admin_items_act)


@dp.callback_query_handler(AdmC(), items_act.filter(act='add'))
async def add_items(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text('Введите данные о товаре что бы внести его в список\n'
                                 'Ввести надо <b>Название товара, цена (обязательно с точкой), описание (не обязательно), ссылку на фото</b> через строчку\n\n'
                                 'Пример:\n'
                                 'Ананас\n'
                                 '60\n'
                                 'Самый вкусный\n'
                                 'https://images.av.ru/av.ru/product/h53/h1b/8953463635998.jpg',
                                 disable_web_page_preview=True,
                                 reply_markup=button_cancel)
    await ItemsAct.add_wait_text.set()


@dp.message_handler(AdmM(), state=ItemsAct.add_wait_text)
async def add_item(message: types.Message, state: FSMContext):
    try:
        text = message.text.split('\n')
        await message.answer('%s'
                             '<b>Товар:</b> %s\n'
                             '<b>Цена:</b> %s$\n'
                             '<b>Описание:</b>\n%s\n\n'
                             '<i>Дата выставления товара: сейчас</i>' % \
                             (hide_link(text[3]), text[0], text[1], text[2]))
    except Exception:
        await message.answer('Текст заполнен не правильно')
    else:
        await state.update_data(text=text)
        await message.answer('Вы уверены что хотите добавить этот товар?', reply_markup=button_confirm_add)


@dp.callback_query_handler(AdmC(), text='confirm_add', state=ItemsAct.add_wait_text)
async def confirm_add(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    try:
        text = data['text']
        item = Items(name=text[0], price=text[1], description=text[2], thumb_url=text[3])
        async with async_session() as session:
            async with session.begin():
                session.add(item)
    except Exception as err:
        await call.message.edit_text(f'Что-то пошло не так и товар не был добавлен!\n<i>{err}</i>', reply_markup=None)
    else:
        await call.message.edit_text('Товар успешно добавлен!', reply_markup=None)
        await state.finish()


@dp.callback_query_handler(AdmC(), items_act.filter(act='change'))
async def change_items(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text('Пришлите мне через инлайн мод товар который вы хотите изменить', reply_markup=button_cancel)
    await ItemsAct.change_wait_item.set()

def to_(self):
    d = {'name': self.name,
         'description': self.description,
         'price': self.price,
         'thumb_url': self.thumb_url}
    return d

async def get_info_fsm(data):
    info = ['name', 'description', 'price', 'thumb_url']
    acts = {'name': '<b>Название</b>', 'description': '<b>Описание</b>', 'price': '<b>Стоимостью</b>',
            'thumb_url': '<b>Ссылку для фото</b>'}
    old_and_now = ''

    for e in info:
        if data[e] is None:
            old_and_now += ''
        else:
            old_and_now += f'{acts[e]}: <s>{to_(data["old"])[e]}</s> {data[e]}\n'
    return old_and_now


@dp.message_handler(AdmM(), state=ItemsAct.change_wait_item)
async def wait_msg(message: types.Message, state: FSMContext):
    data = await state.get_data()
    for q in ['name', 'description', 'price', 'thumb_url']:
        if q in data:
            await message.answer(f'{await get_info_fsm(data)}Что вы хотите изменить у этого товара?',
                                 reply_markup=change_item_v1, disable_web_page_preview=True)
            return

    if message.via_bot.id != (await dp.bot.me).id:
        await message.answer('Пришлите сообщение через инлайн мод этого бота.')
        return

    id = re.compile('id=(\d)+')
    try:
        id = id.match(message.text, pos=1).group(1)
        id = int(id)
    except AttributeError or ValueError:
        await message.answer('Что-то пошло не так, попробуйте ещё раз.')

    async with async_session() as session:
        results = await session.execute(select(Items).where(Items.id == id))
        item = results.scalars().first()

    if item is None:
        await message.answer('Товар не найден! :/')
        return

    await message.answer('Что вы хотите изменить у этого товара?', reply_markup=change_item)
    await state.update_data(id=id, old=item, name=None, description=None, price=None, thumb_url=None)


@dp.callback_query_handler(AdmC(), item_change.filter(act='save'), state=ItemsAct.change_wait_item)
async def save(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()

    old = data['old']
    for item in ['name', 'description', 'price', 'thumb_url']:
        item_ = data[item]
        if item_ is None:
            continue

        async with async_session() as session:
            stmt = update(Items).where(Items.id == old.id).values({item: item_}). \
                returning(to_(Items)[item])

            await session.execute(stmt)
            await session.commit()

    await call.message.edit_text(f'Товар №{old.id} обновлён', reply_markup=None)
    await state.finish()


@dp.callback_query_handler(AdmC(), item_change.filter(), state=ItemsAct.change_wait_item)
async def item_change_all(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    act = callback_data.get('act')
    acts = {'name': 'е <b>Название</b>', 'description': 'е <b>Описание</b>', 'price': 'ю <b>Стоимость</b>',
            'thumb_url': 'ю <b>Фото</b>'}
    await call.message.edit_text(f'Отправьте ново{acts[act]}', reply_markup=None)
    await state.update_data(act=act)
    await ItemsAct.change_wait_input.set()


@dp.message_handler(AdmM(), state=ItemsAct.change_wait_input)
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
    elif data['act'] == 'thumb_url':
        if message.text[0:8] == 'https://' or message.text[0:7] == 'http://':
            pass
        else:
            await message.answer('Ссылка неправильная!')
            return
    await state.update_data({data['act']: message.text})
    await ItemsAct.change_wait_item.set()
    await wait_msg(message, state)


@dp.callback_query_handler(AdmC(), items_act.filter(act='del'))
async def del_item(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text('Пришлите мне через инлайн мод товар который вы хотите удалить',
                                 reply_markup=button_cancel)
    await ItemsAct.del_wait_item.set()


@dp.message_handler(AdmM(), state=ItemsAct.del_wait_item)
async def wait_del_item(message: types.Message, state: FSMContext):
    if message.via_bot.id != (await dp.bot.me).id:
        await message.answer('Пришлите сообщение через инлайн мод этого бота.')
        return

    id = re.compile('id=(\d)+')
    try:
        id = id.match(message.text, pos=1).group(1)
        id = int(id)
    except AttributeError or ValueError:
        await message.answer('Что-то пошло не так, попробуйте ещё раз.')

    await state.update_data(id=id)
    await message.answer('Вы уверены что хотите <b>удалить этот товар</b>?', reply_markup=button_confirm_del)


@dp.callback_query_handler(AdmC(), text='confirm_del', state=ItemsAct.del_wait_item)
async def delete_item(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    id = (await state.get_data())['id']
    async with async_session() as session:
        results = await session.execute(select(Items).where(Items.id == id))
        item = results.scalars().first()

        if item is None:
            await call.message.edit_text('Товар не найден! :/')
            return

        await session.delete(item)
        await session.commit()

    await call.message.edit_text(f'Товар №{item.id} удалён!')
    await state.finish()


@dp.callback_query_handler(AdmC(), text='cancel', state='*')
async def cancel_callback(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_text('Вы отменили', reply_markup=None)
    await state.finish()


@dp.message_handler(AdmM(), Command('cancel', ignore_case=True))
@dp.message_handler(AdmM(), Command('отмена', ignore_case=True))
async def cancel_message(message: types.Message, state: FSMContext):
    await message.edit_text('Вы отменили', reply_markup=None)
    await state.finish()

