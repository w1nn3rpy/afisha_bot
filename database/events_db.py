import datetime
from typing import List

import asyncpg

from config import logger
from database.models import DB_URL

async def add_events(events:List[dict]):
    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)

        query = '''
        INSERT INTO temp_events_table (title, category, date, location, link)
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


async def get_events_without_description():
    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)
        query = """
        SELECT link FROM temp_events_table
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
        WHERE link = $1'''

        await conn.execute(query, url)

    except Exception as e:
        logger.error(f'Произошла ошибка в {__name__}: {e}')

    finally:
        if conn:
            await conn.close()

async def copy_events_from_release_to_temp_table(point: str):
    if point == 'yandex_afisha':
        url = 'https://afisha.yandex.ru/tomsk'
    elif point == 'afisharu':
        url = 'https://www.afisha.ru'
    elif point == 'ticketland':
        url = 'https://tomsk.ticketland.ru'
    else:
        raise ValueError('Неизвестное значение для URL')

    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)
        rows = await conn.fetch('''
        SELECT * FROM events
        WHERE link LIKE $1 || '%';''', url)

        if not rows:
            logger.info('В таблице events нет данных подходящих под запрос')
            return

        for row in rows:
            try:
                await conn.execute('''
                INSERT INTO temp_events_table (title, category, date, location, description, link)
                VALUES ($1, $2, $3, $4, $5, $6)''',
                                   row['title'], row['category'], row['date'], row['location'], row['description'], row['link'])

                logger.info(f"✅ Успешно перемещена запись: {row['title']} {row['date']}")

            except Exception as row_error:
                logger.error(f"⚠️ Ошибка при перемещении {row['title']} {row['date']}: {row_error}")
                continue  # Пропускаем ошибочную строку

    except Exception as e:
        logger.error(f'❌ Общая ошибка в move_events_from_temp_to_release_table: {e}')

    finally:
        if conn:
            await conn.close()


async def move_events_from_temp_to_release_table():
    """Перемещает события из временной таблицы в основную и всегда очищает temp_events_table."""

    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)

        # Получаем все данные из временной таблицы
        rows = await conn.fetch('SELECT * FROM temp_events_table')

        if not rows:
            logger.info("ℹ️ Временная таблица пуста, перемещение не требуется.")
            return

        # Перебираем строки и перемещаем по одной
        for row in rows:
            try:
                await conn.execute('''
                    INSERT INTO events (title, category, date, location, description, link)
                    VALUES ($1, $2, $3, $4, $5, $6)
                ''', row['title'], row['category'], row['date'], row['location'], row['description'], row['link'])

                logger.info(f"✅ Успешно перемещена запись: {row['title']} {row['date']}")

            except Exception as row_error:
                logger.error(f"⚠️ Ошибка при перемещении {row['title']} {row['date']}: {row_error}")
                continue  # Пропускаем ошибочную строку

    except Exception as e:
        logger.error(f'❌ Общая ошибка в move_events_from_temp_to_release_table: {e}')

    finally:
        if conn:
            try:
                await conn.execute('DELETE FROM temp_events_table')  # Очистка таблицы в любом случае
                logger.info("🗑 Временная таблица очищена.")
            except Exception as cleanup_error:
                logger.error(f"❌ Ошибка при очистке temp_events_table: {cleanup_error}")
            await conn.close()

async def get_user_filters(user_id):
    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)
        query = '''
        SELECT selected_category
        FROM users
        WHERE user_id = $1'''
        row = await conn.fetchval(query, user_id)
        print('row:', row)
        return row

    except Exception as e:
        logger.error(f'Произошла ошибка в {__name__}: {e}')

    finally:
        if conn:
            await conn.close()


async def get_events(user_id, period: str = 'today'):
    conn = None
    today = datetime.date.today()
    filters = await get_user_filters(user_id)

    if period == 'week':
        end_date = today + datetime.timedelta(days=7)
    elif period == 'month':
        end_date = today + datetime.timedelta(days=31)
    else:
        end_date = today

    try:
        conn = await asyncpg.connect(DB_URL)
        no_filter_query = '''
        SELECT e.*
        FROM events e
        LEFT JOIN user_events ue
        ON ue.user_id = $3 and ue.event_id = e.id and ue.visited = TRUE
        WHERE ue.event_id IS NULL
        AND e.date BETWEEN $1 AND $2
        ORDER BY date'''

        filters_query = '''
        SELECT e.* FROM events e
        LEFT JOIN user_events ue
        ON ue.user_id = $4 and ue.event_id = e.id and ue.visited = TRUE
        WHERE ue.event_id IS NULL
        AND e.date BETWEEN $1 AND $2
        AND category = ANY($3)
        ORDER BY date'''

        if filters:
            events = await conn.fetch(filters_query, today, end_date, filters, user_id)
        else:
            events = await conn.fetch(no_filter_query, today, end_date, user_id)

        print('evetns from db: ', events)
        return events

    except Exception as e:
        logger.error(f'Произошла ошибка в {__name__}: {e}')

    finally:
        if conn:
            await conn.close()

async def mark_event_as_visited_db(user_id, event_id):
    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)
        query = '''
        INSERT INTO user_events (user_id, event_id, visited)
        VALUES ($1, $2, TRUE)'''
        await conn.execute(query, user_id, event_id)

    except Exception as e:
        logger.error(f'Произошла ошибка в {__name__}: {e}')

    finally:
        if conn:
            await conn.close()

async def delete_past_events():
    conn = None
    today = datetime.date.today()
    try:
        conn = await asyncpg.connect(DB_URL)
        query = '''
        DELETE FROM events
        WHERE date < $1
        '''
        result = await conn.execute(query, today)
        logger.info(f"Удалено {result} старых событий")


    except Exception as e:
        logger.error(f'Произошла ошибка в {__name__}: {e}')

    finally:
        if conn:
            await conn.close()