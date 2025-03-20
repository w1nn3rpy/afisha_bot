import asyncio
import multiprocessing
from typing import List, Dict, Callable

import os
import psutil
import shutil
import subprocess

from config import logger
from database.events_db import add_events, add_descriptions, get_events_without_description, \
    move_events_from_temp_to_release_table
from parse.ticketland.parse_events import get_all_events_ticketland
from parse.afisharu.parse_events import get_all_events_afisharu
from parse.afisharu.parse_description_of_events import get_event_description_afisharu
from parse.ticketland.parse_description_of_events import get_event_descriptions_ticketland
from parse.yandex_afisha.parse_events import get_all_events_yandex_afisha
from parse.yandex_afisha.parse_description_of_events import get_event_description_yandex_afisha


def run_parallel(func: Callable, urls: List[str], num_processes: int = 2) -> Dict[str, str]:
    """
    Запускает парсинг в несколько процессов и объединяет результаты.
    """
    chunk_size = max(1, len(urls) // num_processes)  # Разбиваем список ссылок на части
    url_chunks = [urls[i:i + chunk_size] for i in range(0, len(urls), chunk_size)]

    logger.info(f"🔄 Запускаем {num_processes} процессов, каждая часть содержит {chunk_size} ссылок...")

    with multiprocessing.Pool(processes=num_processes) as pool:
        results = pool.starmap(func, [(i, chunk) for i, chunk in enumerate(url_chunks)])

    # Объединяем результаты всех процессов в один словарь
    merged_results = {}
    for result in results:
        if result:
            merged_results.update(result)

    return merged_results


async def parse_everyday_ticketland():
    all_events_list_of_dicts = get_all_events_ticketland()
    if all_events_list_of_dicts is not None:
        await add_events(all_events_list_of_dicts)

    list_of_records = await get_events_without_description()
    list_of_links = [record['link'] for record in list_of_records]

    if list_of_links is not None:
        description = run_parallel(get_event_descriptions_ticketland, list_of_links)
        await add_descriptions(description)

    await asyncio.to_thread(clean_up)

    await move_events_from_temp_to_release_table()

async def parse_everyday_afisharu():
    all_events_list_of_dicts = get_all_events_afisharu()
    if all_events_list_of_dicts is not None:
        await add_events(all_events_list_of_dicts)

    list_of_records = await get_events_without_description()
    list_of_links = [record['link'] for record in list_of_records]

    if list_of_links is not None:
        description = run_parallel(get_event_description_afisharu, list_of_links)
        await add_descriptions(description)

    await asyncio.to_thread(clean_up)

    await move_events_from_temp_to_release_table()

async def parse_everyday_yandex_afisha():
    all_events_list_of_dicts = get_all_events_yandex_afisha()
    if all_events_list_of_dicts is not None:
        await add_events(all_events_list_of_dicts)
    #
    # list_of_records = await get_events_without_description()
    # list_of_links = [record['link'] for record in list_of_records]
    #
    # if list_of_links is not None:
    #     # description = run_parallel(get_event_description_yandex_afisha, list_of_links)
    #     description = get_event_description_yandex_afisha(list_of_links)
    #     await add_descriptions(description)

    await asyncio.to_thread(clean_up)

    # await move_events_from_temp_to_release_table()

def clean_up():
    logger.info("🔄 Очистка памяти и завершение процессов...")

    # Закрываем Chrome и Chromedriver
    subprocess.call("pkill -f chrome", shell=True)
    subprocess.call("pkill -f chromedriver", shell=True)

    # Очистка кеша
    subprocess.call("sync; echo 3 > /proc/sys/vm/drop_caches", shell=True)

    # Очистка временных файлов
    tmp_dirs = ["/tmp", "/dev/shm"]
    for d in tmp_dirs:
        try:
            shutil.rmtree(d, ignore_errors=True)
        except Exception as e:
            logger.error(f"Ошибка при очистке {d}: {e}")

    # Удаление зомби-процессов
    for proc in psutil.process_iter():
        try:
            if proc.status() == psutil.STATUS_ZOMBIE:
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    logger.info('✅ Память успешно очищена')

    # Создание папки /tmp, если её нет
    os.makedirs("/tmp", exist_ok=True)

    # Установка прав 1777 (drwxrwxrwt — чтение, запись и выполнение для всех, но удаление только владельцем)
    os.chmod("/tmp", 0o1777)

    logger.info("Папка /tmp создана и права установлены на 1777.")


if __name__ == "__main__":
    asyncio.run(parse_everyday_afisharu())