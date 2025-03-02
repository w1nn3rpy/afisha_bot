import asyncio
import multiprocessing
from typing import List, Dict

from asyncpg import Record

from config import logger
from database.events_db import add_events, add_descriptions, get_events_without_description
from parse.afisha.parse_events import get_all_events
from parse.afisha.parse_description_of_events import get_descriptions

def run_parallel(urls: List[str], num_processes: int = 3) -> Dict[str, str]:
    """
    Запускает парсинг в несколько процессов и объединяет результаты.
    """
    chunk_size = max(1, len(urls) // num_processes)  # Разбиваем список ссылок на части
    url_chunks = [urls[i:i + chunk_size] for i in range(0, len(urls), chunk_size)]

    logger.info(f"🔄 Запускаем {num_processes} процессов, каждая часть содержит {chunk_size} ссылок...")

    with multiprocessing.Pool(processes=num_processes) as pool:
        results = pool.starmap(get_descriptions, [(i, chunk) for i, chunk in enumerate(url_chunks)])
        # results = pool.map(get_descriptions, url_chunks)

    # Объединяем результаты всех процессов в один словарь
    merged_results = {}
    for result in results:
        merged_results.update(result)

    return merged_results


async def parse_everyday_afisha():
    # all_events_list_of_dicts = get_all_events()
    link_of_events = []

    # if all_events_list_of_dicts is not None:
    #     await add_events(all_events_list_of_dicts)

    list_of_records = await get_events_without_description()
    list_of_links = [record['source'] for record in list_of_records]

    if list_of_links is not None:
        description = run_parallel(list_of_links)
        await add_descriptions(description)


if __name__ == "__main__":
    asyncio.run(parse_everyday_afisha())