from typing import List

import asyncpg

from config import logger
from database.models import DB_URL

async def add_events(events:List[dict]):
    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)

        query = '''
        INSERT INTO events (title, category, date, time, location, source)
        VALUES ($1, $2, $3, $4, $5, $6)
        '''

        for event in events:
            try:

                title =  event.get('title')
                category = event.get('category')
                date = event.get('date')
                time = event.get('time')
                location = event.get('location')
                link = event.get('event_link')

                await conn.execute(query, title, category, date, time, location, link)

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
        UPDATE events
        SET descriptions = $2 
        WHERE link = $1'''

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



