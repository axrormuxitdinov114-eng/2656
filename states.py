from aiogram.fsm.state import State, StatesGroup

class AddProductStates(StatesGroup):
    waiting_for_photo = State()
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_category = State()

class OrderStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_address = State()
    waiting_for_confirmation = State()

class BroadcastStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_confirmation = State()