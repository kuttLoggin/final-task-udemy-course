from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import CommandStart
from keyboards.inline.start import start_inline

import utils.db_api.commands as db
from data.config import ADMINS
from loader import dp


@dp.message_handler(CommandStart(), state='*')
async def bot_start(message: types.Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)

    if not user:
        bot_username = (await dp.bot.me).username
        if str(message.from_user.id) in ADMINS:
            admin = await db.verify_admin(message.from_user.id, message.from_user.full_name)

            await message.answer(f'Здравствуйте, новый Администратор {message.from_user.get_mention()}\n'
                                 f'Что бы открыть админ меню, пропишите /admin\n'
                                 f'Ваш реферальный код <pre>{admin.code}</pre>\n'
                                 f'Или ссылка t.me/{bot_username}?start={admin.code}')
            return

        code = message.text if not message.is_command() else message.get_args()

        if not code:
            await message.answer('Чтобы использовать этого бота введите код приглашения, '
                                 'либо пройдите по реферальной ссылке')
            await state.set_state('wait_code')
            return

        referrer = await db.get_user_on_code(message.get_args())

        if referrer:
            referral = await db.add_referral_user(referrer, message.from_user.id,
                                                  message.from_user.full_name)

            await message.answer(f'Вы были приглашены пользователем <b>{referrer.name}</b>\n'
                                 f'Вы можете получить бонус +10₽ если пригласите рефералов\n'
                                 f'Ваш реферальный код <pre>{referral.code}</pre>\n'
                                 f'Или ссылка t.me/{bot_username}?start={referral.code}',
                                 reply_markup=start_inline)
            return True
        else:
            await message.answer('Неверный код приглашения')
            return False

    await message.answer(f"Здравствуйте, {message.from_user.get_mention()}!\n"
                         f"Ваш баланс: {user.balance}")


@dp.message_handler(state='wait_code')
async def invite_code(message: types.Message, state: FSMContext):
    if await bot_start(message):
        await state.finish()
