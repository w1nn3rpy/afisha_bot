import datetime

import asyncpg

from config import logger
from database.models import DB_URL

async def get_user(user_id):
    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)
        query = '''
        SELECT * FROM users
        WHERE user_id = $1;'''
        row = await conn.fetchrow(query, user_id)
        if row:
            return row
        else:
            return None

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if conn:
            await conn.close()

async def create_user(user_id, username):
    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)
        query = '''
        INSERT INTO users (user_id, username)
        VALUES ($1, $2);'''
        await conn.execute(query, user_id, username)

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if conn:
            await conn.close()

async def update_username(user_id, username):
    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)
        query = '''
        UPDATE users
        SET username = $1
        WHERE user_id = $2;'''
        await conn.execute(query, user_id, username)

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if conn:
            await conn.close()

async def toggle_category(user_id, new_user_categories):
    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)
        query = '''
        UPDATE users
        SET selected_category = $1
        WHERE user_id = $2
        '''
        await conn.execute(query, new_user_categories, user_id)

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if conn:
            await conn.close()

async def enable_notifications(user_id, frequency: int):
    conn = None
    today = datetime.date.today()
    try:
        conn = await asyncpg.connect(DB_URL)
        query = '''
        UPDATE users
        SET notifications = TRUE,
            notification_frequency = $2,
            last_notify = $3
        WHERE user_id = $1;'''

        await conn.execute(query, user_id, frequency, today)

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if conn:
            await conn.close()

async def update_last_notify(user_id):
    conn = None
    today = datetime.date.today()

    try:
        conn = await asyncpg.connect(DB_URL)
        query = '''
        UPDATE users
        SET last_notify = $1
        WHERE user_id = $2'''

        await conn.execute(query, today, user_id)

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if conn:
            await conn.close()


async def disable_notifications(user_id):
    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)
        query = '''
        UPDATE users
        SET notifications = FALSE,
            notification_frequency = NULL,
            last_notify = NULL
        WHERE user_id = $1;'''

        await conn.execute(query, user_id)

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if conn:
            await conn.close()

async def get_users_for_notifications():
    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)

        today = datetime.date.today()

        query = '''
        SELECT user_id FROM users
        WHERE notifications is TRUE 
        AND last_notify + notification_frequency * INTERVAL '1 day' = $1
        '''

        row = await conn.fetch(query, today)

        return row

    except Exception as e:
        logger.error(f'Ошибка в {__name__}: {e}')

    finally:
        if conn:
            await conn.close()