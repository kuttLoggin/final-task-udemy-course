import re
import asyncio
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from aiogram.utils.markdown import hide_link
from keyboards.inline.buy import buy_button, buy_item, req_location
from filters.authorized_users import AuthUser
from utils.misc.qiwi import create_bill, check_bill
from states.buy import BuyItem
from loguru import logger
import utils.db_api.commands as db

from data.config import ADMINS
from loader import dp

@dp.message_handler(CommandStart(deep_link=re.compile(r'^item_id-\d+$')), AuthUser())
async def show_item(message: types.Message, deep_link):
    item_id = int(deep_link[0].split('-')[1])

    item = await db.get_item(item_id)

    if item is None:
        await message.answer('Товар который вы заращиваете не существует.')
        return

    await message.answer(f'{hide_link(item.thumb_url)}'
                         f'<b>Товар:</b> {item.name}\n'
                         f'<b>Цена:</b> {item.price}₽\n'
                         f'<b>Описание:</b>\n{item.description}\n\n'
                         f'<i>Дата выставления товара: '
                         f'{item.create_date.strftime("%d-%m-%Y %H:%M")}</i>',
                         reply_markup=buy_button(item_id)
                         )


@dp.callback_query_handler(buy_item.filter())
async def buy_item_(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer(cache_time=60)
    await state.update_data(id=callback_data.get('id'))
    await call.message.answer('Введите количество товара.\n'
                              'Например: 3')
    await BuyItem.wait_quantity_item.set()


@dp.message_handler(state=BuyItem.wait_quantity_item)
async def quantity_item(message: types.Message, state: FSMContext):
    try:
        int(message.text)
    except ValueError:
        await message.answer('Введите количество товара в цифрах.')
        return

    await message.answer('Хорошо, теперь введите адрес доставки (город, улицу, дом, подъезд, квартиру) '
                         'или отправьте мне свою геолокацию нажав на кнопку ниже.',
                         reply_markup=req_location)
    await state.update_data(quantity=int(message.text))
    await BuyItem.wait_address.set()


@dp.message_handler(state=BuyItem.wait_address, content_types=[types.ContentType.LOCATION, types.ContentType.TEXT])
async def address_delivery(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if 'address' in data:
        await state.update_data(address=f"{data['address']}\n"
                                        f"Подробнее: {message.text}")
    elif message.location:
        await state.update_data(address=f"<b>Широта:</b> {message.location.latitude}\n"
                                        f"<b>Долгота:</b> {message.location.longitude}\n"
                                        f"<a href='https://www.google.com/maps/@{message.location.latitude},"
                                        f"{message.location.longitude}'>Гугл карты</a>")
        await message.answer('Так же введите номер подъезда и номер квартиры.',
                             reply_markup=types.ReplyKeyboardRemove())
        return
    else:
        await state.update_data(address=message.text)

    item_id = int(data['id'])
    await message.answer('Записал адрес доставки товара.', reply_markup=types.ReplyKeyboardRemove())

    await message.answer('Осталось оплатить товар.', reply_markup=buy_button(item_id))
    await BuyItem.wait_payment.set()


async def send_msg_admins(item, data: dict, user_mention: str):
    text = (f'{hide_link(item.thumb_url)}'
            f'<b><i>Новая покупка!</i></b>',
            f'<b>От</b> {user_mention}',
            f'<b>Адрес:</b> \n{data["address"]}',
            f'<b>Товар №{item.item_id}</b>: {item.name}',
            f'<b>Цена:</b> {item.price * data["quantity"]}₽',
            f'<b>Количество:</b> {data["quantity"]}',
            f'<b>Описание:</b> \n{item.description}\n',
            f'<i>Дата выставления товара: {item.create_date}</i>')
    for admin in ADMINS:
        try:
            await dp.bot.send_message(chat_id=admin, text='\n'.join(text))
            await asyncio.sleep(1/10)
        except Exception as err:
            logger.info(err)


@dp.callback_query_handler(buy_item.filter(), state=BuyItem.wait_payment)
async def create_invoice(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    item_id = int(callback_data.get('id'))
    data = await state.get_data()
    await state.finish()

    item = await db.get_item(item_id)
    user = await db.get_user(call.from_user.id)

    if not item:
        await call.message.answer('Такого товара нету.', reply_markup=None)
        return

    if user.balance >= item.price * data['quantity']:
        new_balance = user.balance - item.price * data["quantity"]
        await db.update_user({'balance': new_balance}, call.from_user.id)

        await call.message.edit_reply_markup()
        await call.message.answer(f'Вы оплатили товар своим балансом, теперь ваш баланс: {new_balance}',
                                  reply_markup=types.ReplyKeyboardRemove())
        await send_msg_admins(item, data, call.from_user.get_mention())
        return

    await call.message.edit_text('Генерирую ссылку для оплаты...', reply_markup=None)

    bill = await create_bill(amount=item.price*data['quantity']-user.balance)
    if user.balance > 0.0:
        await db.update_user({'balance': 0.0}, call.from_user.id)

    await call.message.edit_text(f'Оплатить товар можно через <b>Qiwi</b>.\n'
                                 f'Оплатить тут: <a href="{bill.pay_url}">*Клик*</a>\n'
                                 f'<b>У вас есть 15 минут что-бы оплатить товар</b>')

    for i in range(179):
        bill_states = await check_bill(bill=bill)
        if bill_states == 'WAITING':
            await asyncio.sleep(5)
            continue
        elif bill_states in ('EXPIRED', 'REJECTED'):
            await db.update_user({'balance': user.balance}, call.from_user.id)
            await call.message.reply(f'Товар не был оплачен или Счёт был отклонён.\n'
                                     f'Деньги за товар были возвращены, ваш баланс: {user.balance}')
        elif bill_states == 'PAID':
            await call.message.edit_text(f'Товар "{item.name}" был оплачен.')
            await send_msg_admins(item, data, call.from_user.get_mention())

            await call.message.answer(f'{hide_link(item.thumb_url)}'
                                      f'Скоро товар "{item.name}" будет доставлен на ваш адрес доставки.')
        else:
            await call.message.reply(f'Товар не был оплачен или произошла какая ошибка.\n'
                                     f'{bill_states:=}')
        return
