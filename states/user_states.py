from aiogram.fsm.state import State, StatesGroup

class UserStates(StatesGroup):
    menu = State()
    select_categories = State()
    get_today_events = State()
    get_week_events = State()
    get_month_events = State()
    subscribe_on_notifications = State()
    control_subscribe = State()
    confirm_unsubscribe = State()