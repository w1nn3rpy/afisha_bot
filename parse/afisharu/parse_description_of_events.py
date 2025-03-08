import re
import time
import shutil
import multiprocessing
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from config import logger
from parse.afisharu.parse_events import init_driver


def get_event_description(url: str) -> Dict[str, str]:
    """Получает описание мероприятия по ссылке."""
    driver = init_driver()
    description = "Нет описания"
    try:
        logger.info(f"Открываем страницу: {url}")
        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        logger.info("Страница загружена!")

        try:
            error_element = driver.find_element(By.CSS_SELECTOR, "h1.error-page__title")
            if "Данная страница не найдена!" in error_element.text:
                logger.warning(f"Страница 404! Пропускаем {url}")
                return {url: description}
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

            if not first_paragraph:
                logger.warning(f"❌ Описание не найдено в `RESTRICT-TEXT`! {url}")
                return {url: "Нет описания"}

            # Берём текст внутри этого контейнера
            description = first_paragraph.text.strip()

            logger.info(f"✅ Описание найдено: {description}")

        except Exception as e:
            logger.error(f"❌ Ошибка при обработке {url}: {e}")


    finally:
        driver.quit()
    return {url: description}


def get_descriptions_parallel(process_id, urls: List[str], num_processes: int = 2) -> Dict[str, str]:
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

