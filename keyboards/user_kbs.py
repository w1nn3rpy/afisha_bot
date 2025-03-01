from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.user_db import get_user


def go_menu_kb():
    inline_kb = [
        [InlineKeyboardButton(text='↩️ Вернуться назад', callback_data='go_menu')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)

async def main_menu_kb(user_id):
    user_data = await get_user(user_id)

    is_subscribed = user_data['notifications']

    inline_kb = InlineKeyboardBuilder()
    inline_kb.button(text='Выбрать категорию событий', callback_data='select_category_of_events')
    inline_kb.button(text='Прислать события на сегодня', callback_data='get_today_events')
    inline_kb.button(text='Прислать события на ближайшую неделю', callback_data='get_week_events')
    inline_kb.button(text='Прислать события на ближайший месяц', callback_data='get_month_events')

    if is_subscribed is False:
        inline_kb.button(text='Подписаться на уведомления', callback_data='subscribe_on_notifications')
    else:
        inline_kb.button(text='Управление подпиской', callback_data='control_subscribe')

    inline_kb.adjust(1)

    return inline_kb.as_markup()

async def select_categories_kb(user_id):
    user_data = await get_user(user_id)
    selected_category = user_data['selected_category']

    available_categories = ['Концерт',
                            'Театр',
                            'Выставка',
                            'Экскурсия',
                            'Для детей',
                            'Мастер-класс',
                            'Наука',
                            'Другое']

    inline_kb = InlineKeyboardBuilder()

    for category_name in available_categories:
        checked = '✅ ' if category_name in selected_category else ''

        inline_kb.button(text=f'{checked}{category_name}', callback_data=f'toggle_category:{category_name}')
    inline_kb.adjust(2)

    inline_kb.row(InlineKeyboardButton(text='↩️ Вернуться назад', callback_data='go_menu'))

    return inline_kb.as_markup()

def select_frequency_of_notifications_kb():
    inline_kb = InlineKeyboardBuilder()
    inline_kb.button(text='Каждые 7 дней', callback_data='select_frequency_of_notifications:7')
    inline_kb.button(text='Каждый месяц', callback_data='select_frequency_of_notifications:31')
    inline_kb.button(text='Вернуться назад ↩️', callback_data='go_menu')
    inline_kb.adjust(1)
    return inline_kb.as_markup()

def control_subscribe_kb(current_frequency):
    frequency_for_change = 31 if current_frequency == 7 else 7
    inline_kb = InlineKeyboardBuilder()
    if frequency_for_change == 31:
        inline_kb.button(text='Получать каждый 31 день', callback_data='change_frequency:31')
    elif frequency_for_change == 7:
        inline_kb.button(text='Получать каждый 7 дней', callback_data='change_frequency:7')

    inline_kb.button(text='Отписаться от уведомлений', callback_data='disable_notifications')
    inline_kb.button(text='Вернуться назад ↩️', callback_data='go_menu')
    inline_kb.adjust(1)
    return inline_kb.as_markup()

def confirm_unsubscribe_kb():
    inline_kb = InlineKeyboardBuilder()
    inline_kb.button(text='Да, отписаться', callback_data='confirm_unsubscribe')
    inline_kb.button(text='Нет, оставить подписку', callback_data='cancel_unsubscribe')
    inline_kb.button(text='Вернуться назад ↩️', callback_data='go_back_fsm')
    inline_kb.adjust(1)
    return inline_kb.as_markup()