from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, Union
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from decouple import config

from database.user_db import get_user, create_user, update_username, toggle_category, enable_notifications, \
    disable_notifications
from config import bot, logger
from keyboards.user_kbs import main_menu_kb, select_categories_kb, go_menu_kb, select_frequency_of_notifications_kb, \
    control_subscribe_kb, confirm_unsubscribe_kb
from states.user_states import UserStates

user_router = Router()

@user_router.callback_query(F.data == 'go_menu')
async def go_menu(call: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.menu)
    await call.message.edit_text('Не знаешь, куда сходить? Выбери себе развлечение нажатием двух кнопок',
                                 reply_markup=await main_menu_kb(call.from_user.id))

@user_router.message(Command('start'))
async def start_command(message: Message, state: FSMContext):
    if state is not None:
        await state.clear()

    user_data = await get_user(message.from_user.id)
    if user_data is None:
        await create_user(message.from_user.id, message.from_user.username)

    elif user_data['username'] != message.from_user.username:
        await update_username(message.from_user.id, message.from_user.username)

    await message.answer('Не знаешь, куда сходить? Выбери себе развлечение нажатием двух кнопок',
                         reply_markup=await main_menu_kb(message.from_user.id))
    await state.set_state(UserStates.menu)

@user_router.callback_query(UserStates.menu)
async def menu_handler(call: CallbackQuery, state: FSMContext):
    if call.data == 'select_category_of_events':
        await state.set_state(UserStates.select_categories)
        await call.message.edit_text(text='Выберите категории', reply_markup=await select_categories_kb(call.from_user.id))

    elif call.data == 'get_today_events':
        # await state.set_state(UserStates.get_today_events)
        await state.clear()
        await call.message.edit_text('Функция ещё в разработке', reply_markup=go_menu_kb())

    elif call.data == 'get_week_events':
        # await state.set_state(UserStates.get_week_events)
        await state.clear()
        await call.message.edit_text('Функция ещё в разработке', reply_markup=go_menu_kb())

    elif call.data == 'get_month_events':
        # await state.set_state(UserStates.get_month_events)
        await state.clear()
        await call.message.edit_text('Функция ещё в разработке', reply_markup=go_menu_kb())


    elif call.data == 'subscribe_on_notifications':

        await state.set_state(UserStates.subscribe_on_notifications)
        await call.message.edit_text('Выберите частоту уведомлений о мероприятиях\n\n'
                                     'Нажимая на кнопку вы соглашаетесь на получение уведомлений о мероприятиях',
                                     reply_markup=select_frequency_of_notifications_kb())



    elif call.data == 'control_subscribe':

        await state.set_state(UserStates.control_subscribe)
        user_data = await get_user(call.from_user.id)
        frequency = user_data['notification_frequency']

        await call.message.edit_text(f'Сейчас вы подписаны на уведомления раз в {frequency} {"дней" if frequency == 7 else "день"}',
                                     reply_markup=control_subscribe_kb(frequency))


@user_router.callback_query(UserStates.select_categories)
async def select_category_of_events(call: CallbackQuery, state: FSMContext):

    selected_category = call.data.split(':')[1]
    user_data = await get_user(call.from_user.id)
    user_categories = user_data['selected_category']

    if selected_category in user_categories:
        user_categories.remove(selected_category)
    else:
        user_categories.append(selected_category)

    await toggle_category(call.from_user.id, user_categories)

    await call.message.edit_reply_markup(reply_markup=await select_categories_kb(call.from_user.id))

@user_router.callback_query(UserStates.subscribe_on_notifications)
async def subscribe_on_notifications(call: CallbackQuery, state: FSMContext):
    period = int(call.data.split(':')[1])
    await enable_notifications(call.from_user.id, period)

    await call.message.edit_text('Вы подписались на уведомления о новых событиях.\n'
                                 f'Уведомления будут приходить раз в {period} {"дней" if period == 7 else "день"}\n'
                                 f'Управлять подпиской можно перейдя в "Управление подпиской"',
                                 reply_markup=await main_menu_kb(call.from_user.id))
    await state.set_state(UserStates.menu)

@user_router.callback_query(UserStates.control_subscribe)
async def control_subscribe(call: CallbackQuery, state: FSMContext):
    if call.data.startswith('change_frequency'):
        new_frequency = int(call.data.split(':')[1])
        await enable_notifications(call.from_user.id, new_frequency)
        await call.message.edit_text(f'Теперь вы будете получать уведомления раз в {new_frequency} {"дней" if new_frequency == 7 else "день"}',
                                     reply_markup=await main_menu_kb(call.from_user.id))
        await state.set_state(UserStates.menu)

    elif call.data == 'disable_notifications':
        await call.message.edit_text('Вы хотите отписаться от уведомлений.\n'
                                     'Вы уверены?',
                                     reply_markup=confirm_unsubscribe_kb())
        await state.set_state(UserStates.confirm_unsubscribe)

@user_router.callback_query(UserStates.confirm_unsubscribe)
async def confirm_unsubscribe(call: CallbackQuery, state: FSMContext):
    if call.data == 'confirm_unsubscribe':
        await disable_notifications(call.from_user.id)
        await call.message.edit_text('Вы отписались от уведомлений',
                                     reply_markup=await main_menu_kb(call.from_user.id))
        await state.set_state(UserStates.menu)

    elif call.data == 'cancel_unsubscribe':
        await call.message.edit_text('Вы оставили подписку на уведомления',
                                     reply_markup=await main_menu_kb(call.from_user.id))
        await state.set_state(UserStates.menu)

    elif call.data == 'go_back_fsm':
        await state.set_state(UserStates.control_subscribe)
        user_data = await get_user(call.from_user.id)
        frequency = user_data['notification_frequency']

        await call.message.edit_text(
            f'Сейчас вы подписаны на уведомления раз в {frequency} {"дней" if frequency == 7 else "день"}',
            reply_markup=control_subscribe_kb(frequency))
