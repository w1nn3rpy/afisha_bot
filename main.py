import asyncio

from config import dp, bot, logger
from database.models import create_table_if_not_exist
from handlers.admin_handlers import set_commands, admin_router
from handlers.user_handlers import user_router
from scheduler import start_scheduler, parse_events_scheduler, delete_past_events_scheduler


async def main():
    await create_table_if_not_exist()
    start_scheduler()
    await delete_past_events_scheduler()
    await parse_events_scheduler()
    dp.include_router(admin_router)
    dp.include_router(user_router)
    await bot.delete_webhook(drop_pending_updates=True)
    await set_commands()
    await dp.start_polling(bot)

try:
    if __name__ == "__main__":
        asyncio.run(main())

except KeyboardInterrupt:
    logger.info('Shutting down')
