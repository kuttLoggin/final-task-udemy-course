from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import CommandStart

import utils.db_api.commands as db
from data.config import ADMINS
from loader import dp


# @dp.message_handler(CommandStart(deep_link='connect_user'), state='*')
# async def connect_user(message: types.Message, state: FSMContext):
#     if str(message.from_user.id) in ADMINS:
#         admin = await db.verify_admin(message.from_user.id, message.from_user.full_name)
#
#         bot_username = (await dp.bot.me).username
#         await message.answer(f'Здравствуйте, новый Администратор {message.from_user.full_name}\n'
#                              f'Что бы открыть админ меню, пропишите /admin\n'
#                              f'Ваш реферальный код <pre>{admin.code}</pre>\n'
#                              f'Или ссылка t.me/{bot_username}?start={admin.code}')
#         return
#
#     await message.answer('Что бы получить доступ к боту, перейдите по инвайт ссылке '
#                          'или введите код приглашения.')
#     await state.set_state('wait_code')


@dp.message_handler(CommandStart(), state='*')
async def bot_start(message: types.Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)

    if not user:
        if str(message.from_user.id) in ADMINS:
            admin = await db.verify_admin(message.from_user.id, message.from_user.full_name)

            bot_username = (await dp.bot.me).username
            await message.answer(f'Здравствуйте, новый Администратор {message.from_user.full_name}\n'
                                 f'Что бы открыть админ меню, пропишите /admin\n'
                                 f'Ваш реферальный код <pre>{admin.code}</pre>\n'
                                 f'Или ссылка t.me/{bot_username}?start={admin.code}')
            return

        code = message.text if message.is_command() else message.get_args()

        if code == '':
            await message.answer('Чтобы использовать этого бота введите код приглашения, '
                                 'либо пройдите по реферальной ссылке')
            await state.set_state('wait_code')
            return

        referrer = await db.get_user_on_code(message.get_args())

        if not referrer:
            return await message.answer('Неверный код приглашения')
        else:
            referral = await db.add_referral_user(referrer, message.from_user.id, message.from_user.full_name)

            bot_username = (await dp.bot.me).username
            await message.answer(f'Вы были приглашены пользователем <b>{referrer.name}</b>\n'
                                 f'Вы можете получить бонус +10₽ если пригласите рефералов\n'
                                 f'Ваш реферальный код <pre>{referral.code}</pre>\n'
                                 f'Или ссылка t.me/{bot_username}?start={referral.code}',
                                 reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                                     types.InlineKeyboardButton(
                                             text='Вперёд за покупками',
                                             switch_inline_query_current_chat=''
                                         )]])
                                 )
        return True

    await message.answer(f"Здравствуйте, {message.from_user.get_mention()}!\n"
                         f"Ваш баланс: {user.balance}")


@dp.message_handler(state='wait_code')
async def invite_code(message: types.Message, state: FSMContext):
    if await bot_start(message):
        await state.finish()
