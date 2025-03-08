import asyncio
import random
import re
import time
import shutil
import multiprocessing
import traceback
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from config import logger
from database.events_db import delete_event_by_url
from parse.afisharu.parse_events import init_driver


def get_event_description(process_id, list_of_links: List[str]) -> Dict[str, str] | None:
    """Получает описание мероприятия по ссылке."""

    descriptions = {url: 'Нет описания' for url in list_of_links}


    all_count = len(list_of_links)
    current_count = 0

    driver = init_driver()
    try:
        for url, description in descriptions.items():
            attempts = 0
            max_attempts = 5

            while attempts < max_attempts:

                logger.info(f"[{process_id}] [INFO] {current_count}/{all_count} Открываем страницу: {url}")
                driver.get(url)
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                logger.info(f"[{process_id}] [INFO] Страница загружена!")

                try:
                    error_element = driver.find_element(By.CSS_SELECTOR, "h1.error-page__title")
                    if "Данная страница не найдена!" in error_element.text:
                        logger.warning(f"[{process_id}] ⚠️ Страница 404! Удаляем {url}")
                        asyncio.run(delete_event_by_url(url))
                        break
                except:
                    pass  # Ошибки нет, продолжаем

                try:
                    # Ждём появления блока описания
                    description_block = WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test='OBJECT-DESCRIPTION-CONTENT']"))
                    )
                    soup = BeautifulSoup(description_block.get_attribute("innerHTML"), "html.parser")

                    # Пробуем найти основной текст внутри RESTRICT-TEXT
                    first_paragraph = soup.find("div", {"data-test": "RESTRICT-TEXT"})

                    if first_paragraph:
                        new_description = first_paragraph.text.strip()
                        logger.info(f"[{process_id}] [INFO] Описание: {new_description}")

                        if len(description) > 5:
                            descriptions[url] = new_description
                        else:
                            logger.info(f"[{process_id}] [INFO] Обнаруженное описание менее 5 символов. Установлено 'Нет описания'")

                    break

                except Exception as e:
                    attempts += 1
                    logger.error(f"[{process_id}] [ERROR {attempts}/{max_attempts}] Ошибка при обработке {url}: {e}")

                    if attempts > 3:
                        asyncio.run(delete_event_by_url(url))
                        logger.warning(f"[{process_id}] [WARNING] Страница {url} не загрузилась! Удаляем из базы.")
                        break

                    driver.quit()
                    time.sleep(5)
                    driver = init_driver()
                    logger.info(f'[{process_id}] [INFO] Браузер перезапущен')
                    time.sleep(5)

            time.sleep(random.uniform(0.5, 2))  # Задержка для избежания бана
            current_count += 1
        logger.info(f'[{process_id}] [INFO] возвращение значений descriptions')
        return descriptions

    except Exception as e:
        logger.error(f"[{process_id}] [ERROR] Произошла ошибка:")
        logger.error(traceback.format_exc())
        return descriptions

    finally:

        if 'driver' in locals():
            driver.quit()
            logger.info(f"[{process_id}] [INFO] Браузер закрыт!")


def get_descriptions_parallel(urls: List[str], num_processes: int = 2) -> Dict[str, str]:
    chunk_size = max(1, len(urls) // num_processes)  # Разбиваем список ссылок на части
    url_chunks = [urls[i:i + chunk_size] for i in range(0, len(urls), chunk_size)]

    logger.info(f"🔄 Запускаем {num_processes} процессов, каждая часть содержит {chunk_size} ссылок...")


    """Запускает сбор описаний в многопроцессорном режиме."""
    with multiprocessing.Pool(processes=num_processes) as pool:  # Используем 2 процесса
        results = pool.starmap(get_event_description, [(i, chunk) for i, chunk in enumerate(url_chunks)])

    # Объединяем результаты всех процессов в один словарь
    merged_results = {}
    for result in results:
        if result:
            merged_results.update(result)

    return merged_results

