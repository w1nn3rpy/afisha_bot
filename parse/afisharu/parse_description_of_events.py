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

BASE_URL = "https://www.afisha.ru/tomsk/events/page{}/performances/exhibitions/concerts/"


def init_driver():
    """Инициализация Selenium WebDriver."""
    CHROME_PATH = shutil.which("google-chrome") or shutil.which("google-chrome-stable")
    if not CHROME_PATH:
        raise FileNotFoundError(
            "Google Chrome не найден! Установите его через 'sudo apt install google-chrome-stable'.")

    CHROMEDRIVER_PATH = shutil.which("chromedriver")
    if not CHROMEDRIVER_PATH:
        raise FileNotFoundError("ChromeDriver не найден! Установите его.")

    chrome_options = Options()
    chrome_options.binary_location = CHROME_PATH
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


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

        description_block = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.formatted-text.mts-text"))
        )

        soup = BeautifulSoup(description_block.get_attribute("innerHTML"), "html.parser")
        first_paragraph = soup.find("p")

        if first_paragraph:
            description = first_paragraph.text.strip()
            logger.info(f"Описание: {description}")

    except Exception as e:
        logger.error(f"Ошибка при обработке {url}: {e}")
    finally:
        driver.quit()
    return {url: description}


def get_descriptions_parallel(urls: List[str], num_processes: int = 2) -> Dict[str, str]:
    chunk_size = max(1, len(urls) // num_processes)  # Разбиваем список ссылок на части
    url_chunks = [urls[i:i + chunk_size] for i in range(0, len(urls), chunk_size)]
    """Запускает сбор описаний в многопроцессорном режиме."""
    with multiprocessing.Pool(processes=num_processes) as pool:  # Используем 2 процесса
        results = pool.starmap(get_event_description, [(i, chunk) for i, chunk in enumerate(url_chunks)])
    descriptions = {k: v for d in results for k, v in d.items()}

    # Объединяем результаты всех процессов в один словарь
    merged_results = {}
    for result in results:
        if result:
            merged_results.update(result)

    return merged_results

