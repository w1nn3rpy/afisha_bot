import asyncpg
from decouple import config
from config import logger

DB_URL=config('DATABASE_URL')

#category TEXT CHECK(category IN('Концерт', 'Театр', 'Выставка', 'Экскурсия', 'Для детей', 'Мастер класс', 'Наука', 'Другое')),


async def create_table_if_not_exist():

    conn = None

    try:
        conn = await asyncpg.connect(DB_URL)
        tables = {
            'users': '''
            CREATE TABLE IF NOT EXISTS users (
            user_id INT8 NOT NULL PRIMARY KEY,
            username VARCHAR(255) DEFAULT NULL,
            notifications BOOLEAN DEFAULT FALSE NOT NULL,
            notification_frequency INT2 CHECK (notification_frequency IN (7, 31)),
            selected_category TEXT[] DEFAULT '{}'
            )''',

            'temp_events_table': '''
            CREATE TABLE temp_events_table (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            category VARCHAR(255) DEFAULT 'Категория не указана',
            date VARCHAR(255) NOT NULL,
            time VARCHAR(255) NOT NULL,
            location TEXT,
            description TEXT DEFAULT 'Нет описания',
            source TEXT,
            UNIQUE (title, date) -- Исключаем дубли по названию и дате
            )''',

            'events': '''
            CREATE TABLE events (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            category VARCHAR(255) DEFAULT 'Категория не указана',
            date VARCHAR(255) NOT NULL,
            time VARCHAR(255) NOT NULL,
            location TEXT,
            description TEXT DEFAULT 'Нет описания',
            source TEXT,
            UNIQUE (title, date) -- Исключаем дубли по названию и дате
            )''',

            'user_events': '''
            CREATE TABLE user_events (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
            event_id INT REFERENCES events(id) ON DELETE CASCADE,
            visited BOOLEAN DEFAULT FALSE,
            UNIQUE (user_id, event_id) -- Исключаем повторную отметку посещения
            )'''
        }



        for table_name, create_sql in tables.items():
            table_exists = await conn.fetchval(f'''
            SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = $1)
            ''', table_name)
            if not table_exists:
                await conn.execute(create_sql)
                logger.info(f'Таблица {table_name} успешно создана!')
            else:
                logger.info(f'Таблица {table_name} уже существует!')

    finally:
        if conn:
            await conn.close()