import asyncio
import os
import random
import time
import traceback
from typing import Dict

import requests
import undetected_chromedriver as uc
from asyncpg import Record
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import logger
from database.events_db import delete_event_by_url


async def get_descriptions(list_of_links: list[Record]) -> Dict[str, str] | None:

    descriptions = {record['source']: 'None' for record in list_of_links}
    all_count = len(list_of_links)
    current_count = 0

    # 🖥 Запуск виртуального дисплея Xvfb (если вдруг не запущен)
    os.system("Xvfb :99 -screen 0 1920x1080x24 &")
    os.environ["DISPLAY"] = ":99"

    # 🚀 Настройки браузера
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")

    try:
        logger.info("[INFO] Запускаем браузер...")
        driver = uc.Chrome(options=options)
        for url, description in descriptions.items():
            attempts = 0
            max_attempts = 5

            while attempts < max_attempts:
                try:
                    logger.info(f"{current_count}/{all_count} [INFO] Открываем страницу: {url}")
                    driver.get(url)

                    # Ожидание полной загрузки страницы
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    logger.info("[INFO] Страница загружена!")

                    # Проверяем статус загрузки
                    status_code = driver.execute_script("return document.readyState")  # "complete" = 200 OK
                    logger.info(f"[INFO] Статус-код {url}: {status_code}")

                    if status_code != 'complete':
                        await delete_event_by_url(url)
                        logger.warning(f"[WARNING] Страница {url} не загрузилась! Удаляем из базы.")
                        break

                    # Ищем блок описания
                    description_block = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.formatted-text.mts-text"))
                    )
                    description = description_block.text.strip()

                    logger.info(f"[INFO] Описание: {description}")
                    descriptions[url] = description
                    break

                except Exception as e:
                    attempts += 1
                    logger.error(f"[ERROR {attempts}/{max_attempts}] Ошибка при обработке {url}: {e}")
                    driver.quit()
                    await asyncio.sleep(5)
                    # 🚀 Настройки браузера
                    options = uc.ChromeOptions()
                    options.add_argument("--no-sandbox")
                    options.add_argument("--disable-gpu")
                    options.add_argument("--disable-dev-shm-usage")
                    options.add_argument("--disable-blink-features=AutomationControlled")

                    driver = uc.Chrome(options=options)
                    logger.info('[INFO] Браузер перезапущен')
                    await asyncio.sleep(5)

            current_count += 1
            await asyncio.sleep(1)

        return descriptions

    except Exception as e:
        logger.error("[ERROR] Произошла ошибка:")
        logger.error(traceback.format_exc())

    finally:
        if 'driver' in locals():
            driver.quit()
            logger.info("[INFO] Браузер закрыт!")
