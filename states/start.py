from aiogram.dispatcher.filters.state import StatesGroup, State


class Start(StatesGroup):
    wait_id = State()
