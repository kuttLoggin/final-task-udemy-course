from aiogram.dispatcher.filters.state import StatesGroup, State

class BuyItem(StatesGroup):
    wait_quantity_item = State()
    wait_address = State()
    wait_payment = State()
