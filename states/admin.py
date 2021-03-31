from aiogram.dispatcher.filters.state import StatesGroup, State

class ItemsAct(StatesGroup):
    add_wait_text = State()
    change_wait_item = State()
    change_wait_input = State()
    del_wait_item = State()
