import asyncio

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, Union, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from decouple import config

from database.events_db import get_events
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

    # elif call.data == 'get_today_events':
    #     # await state.set_state(UserStates.get_today_events)
    #     # await state.clear()
        # await call.message.edit_text('Функция ещё в разработке', reply_markup=go_menu_kb())
        # events = await get_events('today')


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


@user_router.message(Command("events"))
async def show_events(message: Message):
    """Хендлер для отправки первых 10 мероприятий."""
    period = 'week'
    events = await get_events(period)

    if not events:
        await message.answer("⚠️ Нет мероприятий на выбранный период.")
        return

    await send_events_batch(message, events, 0, period)


async def send_events_batch(message, events, page, period):
    """Функция отправки 10 мероприятий по одному в сообщении."""
    per_page = 10
    start_idx = page * per_page
    end_idx = start_idx + per_page
    batch = events[start_idx:end_idx]

    if not batch:
        await message.answer("⚠️ Нет больше мероприятий.")
        return

    for event in batch:
        date = event['date'].strftime('%d.%m.%Y')
        text = (f"🎟 <b>{event['title']}</b>\n"
                f"⭐️ <b>{event['category']}</b>\n"
                f"📅 <b>{date}</b>\n"
                f"📍 <b>{event['location']}</b>\n"
                f"<b>Описание</b>: {event['description']}\n"
                f"🔗 <a href='{event['link']}'>Подробнее</a>\n\n")

        await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)
        await asyncio.sleep(0.5)

    # Добавляем кнопки пагинации только под последним сообщением
    total_pages = (len(events) + per_page - 1) // per_page  # Количество страниц
    buttons = []

    if page > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"events_page:{page - 1}:{period}"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton(text="➡️ Вперёд", callback_data=f"events_page:{page + 1}:{period}"))

    # Создаем клавиатуру только если есть кнопки
    if buttons:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        await message.answer(f"📜 Страница {page + 1} из {total_pages}", reply_markup=keyboard)
    else:
        await message.answer(f"📜 Страница {page + 1} из {total_pages}")


@user_router.callback_query(F.data.startswith("events_page:"))
async def paginate_events(callback: CallbackQuery):
    """Обработчик кнопок пагинации."""
    page = int(callback.data.split(":")[1])
    period = callback.data.split(":")[2]
    events = await get_events(period)

    if page < 0 or page * 10 >= len(events):
        await callback.answer("⚠️ Нет больше мероприятий.", show_alert=True)
        return

    await callback.message.delete()  # Удаляем предыдущее сообщение с кнопками
    await send_events_batch(callback.message, events, page, period)