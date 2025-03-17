import asyncio
import os
import random
import time
import traceback
import tempfile
from typing import List, Dict

import undetected_chromedriver as uc
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from config import logger
from database.events_db import delete_event_by_url
from parse.common_funcs import log_memory_usage


def init_driver(process_id):
    # Создаем уникальную папку для каждого процесса
    user_data_dir = tempfile.mkdtemp(prefix=f"chrome_profile_{process_id}_")

    # Создаем уникальный путь для undetected_chromedriver
    uc_patcher_dir = f"/usr/src/app/chromedriver{process_id}"
    os.makedirs(uc_patcher_dir, exist_ok=True)

    existing_driver = os.path.join(uc_patcher_dir, "chromedriver")

    """Создает и настраивает Chrome для парсинга."""
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--user-data-dir={user_data_dir}")
    options.add_argument("--profile-directory=Default")
    prefs = {
        "profile.managed_default_content_settings.images": 2,  # Выключаем загрузку картинок
        "profile.default_content_setting_values.notifications": 2,  # Выключаем всплывающие окна
        "profile.default_content_setting_values.geolocation": 2,  # Запрещаем геолокацию
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--blink-settings=imagesEnabled=false")  # Отключаем загрузку изображений

    port = 9222 + process_id  # Разные порты для разных процессов

    driver = uc.Chrome(options=options,
                       driver_executable_path=existing_driver,
                       port=port,
                       use_subprocess=True)

    logger.info(f"[{process_id}] Инициализация драйвера...")

    return driver

def get_event_description_yandex_afisha(process_id, list_of_links: List[str]) -> Dict[str, str] | None:
    """Получает описание мероприятия по ссылке."""

    descriptions = {url: 'Нет описания' for url in list_of_links}


    all_count = len(list_of_links)
    current_count = 1

    # 🖥 Запуск виртуального дисплея Xvfb (если вдруг не запущен)
    display_num = 99 + process_id  # Разные Xvfb для каждого процесса
    os.system(f"Xvfb :{display_num} -screen 0 1920x1080x24 &")
    os.environ["DISPLAY"] = f":{display_num}"

    driver = init_driver(process_id)
    try:
        for url, description in descriptions.items():
            log_memory_usage()

            attempts = 1
            max_attempts = 5

            while attempts < max_attempts:

                logger.info(f"[{process_id}] [INFO] ℹ️  {current_count}/{all_count} Открываем страницу: {url}")
                driver.get(url)
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                logger.info(f"[{process_id}] [INFO] ℹ️  Страница загружена!")

                try:
                    # Проверяем наличие элемента с текстом "Ошибка 404" в error-page__body
                    error_body = driver.find_element(By.CSS_SELECTOR, "body.error-page__body")
                    error_text = error_body.find_element(By.CSS_SELECTOR, "div.ErrorTitle-wvicct-11").text

                    if "Ошибка 404" in error_text or "Такой страницы не существует" in error_text:
                        logger.warning(f"[{process_id}] ⚠️ Страница 404! Удаляем {url}")
                        asyncio.run(delete_event_by_url(url))
                        break

                except NoSuchElementException:
                    pass  # Ошибки нет, продолжаем

                try:
                    # Ждём появления блока описания на странице
                    description_block = WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test-id='eventInfo.description']"))
                    )

                    soup = BeautifulSoup(description_block.get_attribute("innerHTML"), "html.parser")

                    # Пробуем найти текст описания внутри div class="tlWAxz"
                    description_element = soup.find("div", class_="tlWAxz")

                    if description_element:
                        new_description = description_element.text.strip()
                        logger.info(f"[{process_id}] [INFO] ✅ Описание: {new_description}")

                        if len(new_description) > 5:
                            descriptions[url] = new_description
                        else:
                            logger.info(f"[{process_id}] [INFO] ℹ️  Обнаруженное описание менее 5 символов. Установлено 'Нет описания'")

                    else:
                        logger.warning(f"[{process_id}] ⚠️ Описание не найдено.")
                        descriptions[url] = "Нет описания"

                    break

                except Exception as e:
                    attempts += 1
                    logger.error(f"[{process_id}] [ERROR {attempts}/{max_attempts}] ❌ Ошибка при обработке {url}: {e}")

                    if attempts > 3:
                        asyncio.run(delete_event_by_url(url))
                        logger.warning(f"[{process_id}] [WARNING] ⚠️ Страница {url} не загрузилась! Удаляем из базы.")
                        break

                    driver.delete_all_cookies()
                    driver.quit()
                    time.sleep(5)
                    driver = init_driver(process_id)
                    logger.info(f'[{process_id}] [INFO] ℹ️  Браузер перезапущен')
                    time.sleep(5)

            time.sleep(random.uniform(0.5, 2))  # Задержка для избежания бана
            current_count += 1
        logger.info(f'[{process_id}] [INFO] ℹ️  Возвращение значений descriptions')
        return descriptions

    except Exception as e:
        logger.error(f"[{process_id}] [ERROR] ❌ Произошла ошибка:")
        logger.error(traceback.format_exc())
        return descriptions

    finally:

        if 'driver' in locals():
            driver.quit()
            logger.info(f"[{process_id}] [INFO] ℹ️  Браузер закрыт!")
