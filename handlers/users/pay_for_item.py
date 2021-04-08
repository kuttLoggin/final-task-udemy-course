import re
from asyncio import sleep
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from aiogram.utils.markdown import hide_link
from sqlalchemy import update
from sqlalchemy.future import select
from data.config import ADMINS
from keyboards.inline.buy import buy_button, buy_item
from filters.authorized_users import AuthUserM
from loader import dp
from utils.db_api.db import async_session
from utils.db_api.models import Items, Users
from utils.misc.qiwi import create_bill, check_bill
from states.buy import BuyItem
from utils.misc import db_commands as db

@dp.message_handler(CommandStart(deep_link=re.compile('^item_id-\d+$')), AuthUserM())
async def show_item(message: types.Message):
    item_id = int(message.get_args().split('-')[1])
    async with async_session() as session:
        results = await session.execute(select(Items).where(Items.item_id == item_id))
        item = results.scalars().first()

    if item is None:
        await message.answer('Такого товара нету.')
        return

    await message.answer('%s'
                         '<b>Товар:</b> %s\n'
                         '<b>Цена:</b> %s₽\n'
                         '<b>Описание:</b>\n%s\n\n'
                         '<i>Дата выставления товара: %s</i>' % \
                         (hide_link(item.thumb_url), item.name, item.price,
                          item.description, item.create_date.strftime('%d-%m-%Y %H:%M')),
                         reply_markup=buy_button(item_id)
                         )
    print(item_id)


@dp.callback_query_handler(buy_item.filter())
async def buy_item_(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer(cache_time=60)
    await state.update_data(id=callback_data.get('id'))
    await call.message.answer('Введите количество товара.\n'
                              'Только число.')
    await BuyItem.wait_quantity_item.set()


@dp.message_handler(state=BuyItem.wait_quantity_item)
async def quantity_item(message: types.Message, state: FSMContext):
    try:
        int(message.text)
    except ValueError:
        await message.answer('Введите количество товара в цифрах.')
        return

    await state.update_data(quantity=message.text)
    await message.answer('Хорошо, теперь введите адрес (город, дом, подъезд, квартиру) доставки или отправьте мне свою геолокацию',
                         reply_markup=types.ReplyKeyboardMarkup(
                             keyboard=[
                                 [
                                     types.KeyboardButton(
                                         text='Отправить геолокацию',
                                         request_location=True
                                     )
                                 ]
                             ],
                             one_time_keyboard=True,
                             resize_keyboard=True
                         ))
    await BuyItem.wait_address.set()


@dp.message_handler(state=BuyItem.wait_address, content_types=[types.ContentType.LOCATION, types.ContentType.TEXT])
async def address_delivery(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if 'address' in data:
        await state.update_data(address=f"{data['address']}\n"
                                        f"Подробнее: {message.text}")
    if message.location:
        await state.update_data(address=f"<b>Широта:</b> {message.location.latitude} \n"
                                        f"<b>Долгота:</b> {message.location.longitude}\n"
                                        f"<a href='https://www.google.com/maps/@{message.location.latitude},{message.location.longitude}'>Гугл карты</a>")
        await message.answer('Так же введите подъед и квартиру', reply_markup=types.ReplyKeyboardRemove())
        return
    else:
        await state.update_data(address=message.text)
    item_id = int((await state.get_data())['id'])
    await message.answer('Хорошо, записал.', reply_markup=types.ReplyKeyboardRemove())
    await message.answer('Осталось оплатить товар', reply_markup=buy_button(item_id))
    await BuyItem.wait_payment.set()


async def send_msg_admins(item, data, call):
    for admin in ADMINS:
        try:
            await dp.bot.send_message(chat_id=admin, text=f'{hide_link(item.thumb_url)}'
                                                          f'<b><i>Новая покупка!</i></b>\n'
                                                          f'<b>От</b> {call.from_user.get_mention()}\n'
                                                          f'<b>Адрес:</b> \n{data["address"]}\n'
                                                          f'<b>Товар №{item.item_id}</b>: {item.name}\n'
                                                          f'<b>Цена:</b> {item.price * data["quantity"]}₽\n'
                                                          f'<b>Количество:</b> {data["quantity"]}\n'
                                                          f'<b>Описание:</b> \n{item.description}\n\n'
                                                          f'<i>Дата выставления товара: {item.create_date}</i>')
        except:
            pass


@dp.callback_query_handler(buy_item.filter(), state=BuyItem.wait_payment)
async def create_invoice(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    item_id = int(callback_data.get('id'))
    data = await state.get_data()

    item = await db.select_item(item_id)
    user = await db.select_user(call.from_user.id)

    # async with async_session() as session:
    #     results = await session.execute(select(Items).where(Items.item_id == item_id))
    #     item = results.scalars().first()
    #
    #     results_ = await session.execute(select(Users).where(Users.user_id == call.from_user.id))
    #     user = results_.scalars().first()

    if not item:
        await call.message.answer('Такого товара нету.', reply_markup=None)
        await state.finish()
        return

    if user.balance >= item.price * int(data['quantity']):
            # stmt = update(Users).where(Users.user_id == call.from_user.id).values(balance=user.balance - item.price*data["quantity"]). \
            #     returning(Users.balance)
            # await session.execute(stmt)
            # await session.commit()
        await db.update_user({'balance': 'user.balance - item.price*data["quantity"]'}, call)

        await call.message.edit_reply_markup()
        await state.finish()
        await call.message.answer(f'Вы оплатили товар своим балансом, теперь ваш баланс: {user.balance}', reply_markup=types.ReplyKeyboardRemove())
        await send_msg_admins(item, data, call)
        return

    await call.message.edit_text('Генерирую ссылку для оплаты...', reply_markup=None)

    bill = await create_bill(amount=item.price*int(data['quantity'])-user.balance)

    await call.message.edit_text(f'Купить товар можно через <b>Qiwi</b>\n'
                                 f'Оплатить тут: <a href="{bill.pay_url}">*Клик*</a>\n'
                                 f'<b>У вас есть 15 минут что-бы оплатить товар</b>')
    await state.finish()

    for i in range(180):
        result = await check_bill(bill=bill)
        if result is False:
            await sleep(5)
            continue
        else:
            await call.message.edit_text('Вижу что вы оплатили товар.')
            await send_msg_admins(item, data, call)
            break
    else:
        await call.message.answer('Товар не был оплачен.')
        return
    await call.message.answer(f'{hide_link(item.thumb_url)}'
                              f'Скоро товар "{item.name}" будет доставлен на адрес доставки.')
