import asyncio
import os
import random
import tempfile
import time
import traceback
from typing import Dict, List

import requests
import undetected_chromedriver as uc
from asyncpg import Record
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import logger
from database.events_db import delete_event_by_url


def init_driver(process_id):
    # Уникальный профиль для каждого процесса
    # Создаем уникальную папку для каждого процесса
    user_data_dir = tempfile.mkdtemp(prefix=f"chrome_profile_{process_id}_")

    # Создаем уникальный путь для undetected_chromedriver
    uc_patcher_dir = f"/root/git/afisha_bot/chromedriver{process_id}"
    os.makedirs(uc_patcher_dir, exist_ok=True)

    # # Если в этой папке уже есть файл драйвера — удаляем, чтобы избежать блокировки
    existing_driver = os.path.join(uc_patcher_dir, "chromedriver")
    # if os.path.exists(existing_driver):
    #     try:
    #         os.remove(existing_driver)
    #     except Exception:
    #         pass  # Игнорируем ошибку удаления, если процесс его уже использует

    """Создает и настраивает Chrome для парсинга."""
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--user-data-dir={user_data_dir}")

    port = 9222 + process_id  # Разные порты для разных процессов

    driver = uc.Chrome(options=options,
                       driver_executable_path=existing_driver,
                       port=port,
                       use_subprocess=True)

    # driver = uc.Chrome(options=options,
    #                    driver_executable_path=existing_driver if os.path.exists(existing_driver) else None,
    #                    use_subprocess=True)

    logger.info(f"[{process_id}] Инициализация драйвера...")

    return driver

def get_descriptions(process_id, list_of_links: List[str]) -> Dict[str, str] | None:

    descriptions = {url: 'Нет описания' for url in list_of_links}

    all_count = len(list_of_links)
    current_count = 0

    # 🖥 Запуск виртуального дисплея Xvfb (если вдруг не запущен)
    os.system("Xvfb :99 -screen 0 1920x1080x24 &")
    os.environ["DISPLAY"] = ":99"

    try:
        logger.info(f"[{os.getpid()}] [INFO] Запускаем браузер...")
        driver = init_driver(process_id)
        for url, description in descriptions.items():
            attempts = 0
            max_attempts = 5

            while attempts < max_attempts:
                try:
                    logger.info(f"{current_count}/{all_count} [{os.getpid()}] [INFO] Открываем страницу: {url}")
                    driver.get(url)

                    # Ожидание полной загрузки страницы
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    logger.info(f"[{os.getpid()}] [INFO] Страница загружена!")

                    # Ищем блок описания
                    description_block = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.formatted-text.mts-text"))
                    )

                    # Извлекаем HTML содержимое блока
                    soup = BeautifulSoup(description_block.get_attribute("innerHTML"), "html.parser")

                    # Находим первый абзац <p> внутри блока
                    first_paragraph = soup.find("p")

                    if first_paragraph:
                        description = first_paragraph.text.strip()

                    logger.info(f"[{os.getpid()}] [INFO] Описание: {description}")

                    if len(description) > 5:
                        descriptions[url] = description
                    else:
                        logger.info(f"[{os.getpid()}] [INFO] Обнаруженное описание менее 5 символов. Установлено 'Нет описания'")

                    break

                except Exception as e:
                    attempts += 1
                    logger.error(f"[{os.getpid()}] [ERROR {attempts}/{max_attempts}] Ошибка при обработке {url}: {e}")

                    # Проверяем статус загрузки
                    status_code = driver.execute_script("return document.readyState")  # "complete" = 200 OK
                    logger.info(f"[{os.getpid()}] [INFO] Статус-код {url}: {status_code}")

                    if attempts > 3 and status_code != 'complete':
                        asyncio.run(delete_event_by_url(url))
                        logger.warning(f"[{os.getpid()}] [WARNING] Страница {url} не загрузилась! Удаляем из базы.")
                        break

                    driver.quit()
                    time.sleep(5)
                    driver = init_driver()
                    logger.info(f'[{os.getpid()}] [INFO] Браузер перезапущен')
                    time.sleep(5)

            time.sleep(random.uniform(0.5, 2))  # Задержка для избежания бана
            current_count += 1

        return descriptions

    except Exception as e:
        logger.error(f"[{os.getpid()}] [ERROR] Произошла ошибка:")
        logger.error(traceback.format_exc())

    finally:
        if 'driver' in locals():
            driver.quit()
            logger.info(f"[{os.getpid()}] [INFO] Браузер закрыт!")
