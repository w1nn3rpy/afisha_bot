import asyncio

from config import dp, bot, logger
from database.models import create_table_if_not_exist
from handlers.admin_handlers import set_commands, admin_router
from handlers.user_handlers import user_router
from parse.parse_everyday import parse_everyday_ticketland, parse_everyday_afisharu, clean_up
from parse.afisharu.parse_events import get_all_events_afisharu



async def main():
    await create_table_if_not_exist()
    dp.include_router(admin_router)
    dp.include_router(user_router)
    await bot.delete_webhook(drop_pending_updates=True)
    await set_commands()
    # await parse_everyday_afisharu()
    await parse_everyday_ticketland()
    await asyncio.to_thread(clean_up())
    await dp.start_polling(bot)

try:
    if __name__ == "__main__":
        asyncio.run(main())

except KeyboardInterrupt:
    logger.info('Shutting down')
