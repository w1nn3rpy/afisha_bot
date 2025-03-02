import asyncio
import multiprocessing
from typing import List, Dict

from asyncpg import Record

from database.events_db import add_events, add_descriptions, get_events_without_description
from parse.afisha.parse_events import get_all_events
from parse.afisha.parse_description_of_events import get_descriptions

def run_parallel(urls: List[str], num_processes=4):
    """Запускает парсинг в несколько процессов."""
    with multiprocessing.Pool(processes=num_processes) as pool:
        results = pool.map(get_descriptions, urls)
    return results


async def parse_everyday_afisha():
    # all_events_list_of_dicts = get_all_events()
    link_of_events = []

    # if all_events_list_of_dicts is not None:
    #     await add_events(all_events_list_of_dicts)

    list_of_records = await get_events_without_description()
    list_of_links = [record['source'] for record in list_of_records]

    if list_of_links is not None:
        description = await run_parallel(list_of_links)
        await add_descriptions(description)


if __name__ == "__main__":
    asyncio.run(parse_everyday_afisha())