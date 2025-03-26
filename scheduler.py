from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database.user_db import get_users_for_notifications, update_last_notify
from database.events_db import delete_past_events
from config import bot, logger
from keyboards.user_kbs import go_menu_button
from parse.parse_everyday import parse_everyday_afisharu, parse_everyday_ticketland, parse_everyday_yandex_afisha, \
    parse_everyday_gorodzovet


async def notify_user_scheduler():
    users_for_notify = await get_users_for_notifications()
    if users_for_notify:
        for user in users_for_notify:
            user_id = user['user_id']
            try:
                await bot.send_message(chat_id=user_id,
                                      text='Добрый день! Появилось много новых мероприятий!\n'
                                           'Посмотрите сейчас!', reply_markup=go_menu_button())
                await update_last_notify(user_id)

            except Exception as e:
                logger.error(f'Ошибка при попытке оповещения пользователя: {e}')
                continue

async def parse_afisharu_scheduler():
    await bot.send_message(chat_id=5983514379, text='Начинаю парсить афишару')
    await parse_everyday_afisharu()
    await bot.send_message(chat_id=5983514379, text='Закончил парсить афишару')

async def parse_ticketland_scheduler():
    await bot.send_message(chat_id=5983514379, text='Начинаю парсить тикетленд')
    await parse_everyday_ticketland()
    await bot.send_message(chat_id=5983514379, text='Закончил парсить тикетленд')

async def parse_yandex_afisha_scheduler():
    await bot.send_message(chat_id=5983514379, text='Начинаю парсить яндекс афишу')
    await parse_everyday_yandex_afisha()
    await bot.send_message(chat_id=5983514379, text='Закончил парсить яндекс афишу')

async def parse_gorodzovet_scheduler():
    await bot.send_message(chat_id=5983514379, text='Начинаю парсить городзовет')
    await parse_everyday_gorodzovet()
    await bot.send_message(chat_id=5983514379, text='Закончил парсить городзовет')


async def delete_past_events_scheduler():
    await delete_past_events()

def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(delete_past_events_scheduler, CronTrigger(hour=9), misfire_grace_time=180)
    scheduler.add_job(notify_user_scheduler, CronTrigger(hour=10), misfire_grace_time=180)
    scheduler.add_job(parse_afisharu_scheduler, CronTrigger(day='*/3', hour=20), misfire_grace_time=180)
    scheduler.add_job(parse_ticketland_scheduler, CronTrigger(day='*/4', hour=21), misfire_grace_time=180)
    scheduler.add_job(parse_gorodzovet_scheduler, CronTrigger(day='*/5', hour=24), misfire_grace_time=180)
    scheduler.add_job(parse_yandex_afisha_scheduler, CronTrigger(day='*/7', hour=22), misfire_grace_time=180)
    scheduler.start()