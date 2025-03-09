from typing import List

import asyncpg

from config import logger
from database.models import DB_URL

async def add_events(events:List[dict]):
    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)

        query = '''
        INSERT INTO temp_events_table (title, category, date, location, source)
        VALUES ($1, $2, $3, $4, $5)
        '''

        for event in events:
            try:

                title =  event.get('title')
                category = event.get('category')
                date = event.get('date')
                location = event.get('venue')
                link = event.get('link')

                await conn.execute(query, title, category, date, location, link)

            except Exception as e:
                logger.error(f'Произошла ошибка в {__name__} при добавлении события: {event}\nОшибка: {e}')


    except Exception as e:
        logger.error(f'Произошла ошибка в {__name__}: {e}')

    finally:
        if conn:
            await conn.close()

async def add_descriptions(descriptions:dict):
    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)

        query = '''
        UPDATE temp_events_table
        SET description = $2 
        WHERE source = $1'''

        for url, description in descriptions.items():
            try:
                await conn.execute(query, url, description)

            except Exception as e:
                logger.error(f'Произошла ошибка в {__name__} при добавлении описания: {description}\nОшибка: {e}')

    except Exception as e:
        logger.error(f'Произошла ошибка в {__name__}: {e}')

    finally:
        if conn:
            await conn.close()


async def get_events_without_description():
    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)
        query = """
        SELECT source FROM temp_events_table
        WHERE description = 'Нет описания'
        """
        rows = await conn.fetch(query)

        return rows if rows is not None else None

    except Exception as e:
        logger.error(f'Произошла ошибка в {__name__}: {e}')

    finally:
        if conn:
            await conn.close()

async def delete_event_by_url(url):
    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)
        query = '''
        DELETE FROM temp_events_table
        WHERE source = $1'''

        await conn.execute(query, url)

    except Exception as e:
        logger.error(f'Произошла ошибка в {__name__}: {e}')

    finally:
        if conn:
            await conn.close()

async def move_events_from_temp_to_release_table():
    """Перемещает события из временной таблицы в основную в транзакции."""
    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)

        async with conn.transaction():  # Безопасная транзакция
            await conn.execute('''
                INSERT INTO events (title, category, date, location, description, source)
                SELECT title, category, date, location, description, source
                FROM temp_events_table;
            ''')

            await conn.execute('''
                DELETE FROM temp_events_table;
            ''')

        logger.info("✅ Данные успешно перемещены из temp_events_table в events")

    except Exception as e:
        logger.error(f'❌ Ошибка в move_events_from_temp_to_release_table: {e}')

    finally:
        if conn:
            await conn.close()