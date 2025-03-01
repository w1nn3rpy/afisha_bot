import asyncio
import os
import random
import time
import traceback
from typing import Dict

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import logger


def get_descriptions(list_of_links: list) -> Dict[str, str] | None:

    descriptions = {link: 'None' for link in list_of_links}
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
        for url in list_of_links:
            try:
                logger.info(f"{current_count}/{all_count} [INFO] Открываем страницу: {url}")
                driver.get(url)

                # Ожидание полной загрузки страницы
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                logger.info("[INFO] Страница загружена!")

                # Ищем блок описания
                try:
                    description_block = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.formatted-text.mts-text"))
                    )
                    description = description_block.text.strip()
                except:
                    logger.error(f"[ERROR] Ошибка при обработке {url}: {e}")
                    description = "Нет описания"

                logger.info(f"[INFO] Описание: {description}")
                descriptions[url] = description

            except Exception as e:

                logger.error(f"[ERROR] Ошибка при обработке {url}: {e}")

                descriptions[url] = "Нет описания"

            current_count += 1
            asyncio.sleep(3)

        return descriptions

    except Exception as e:
        logger.error("[ERROR] Произошла ошибка:")
        logger.error(traceback.format_exc())

    finally:
        if 'driver' in locals():
            driver.quit()
            logger.info("[INFO] Браузер закрыт!")
