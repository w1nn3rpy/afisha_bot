import asyncio
import os
import random
import shutil
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
from parse.yandex_afisha.parse_events import scroll_down


# def init_driver(process_id):
#
#     # """Инициализация WebDriver с обработкой ошибок."""
#     # CHROME_PATH = shutil.which("google-chrome") or shutil.which("google-chrome-stable")
#     # if not CHROME_PATH:
#     #     raise FileNotFoundError(
#     #         "Google Chrome не найден! Установите его через 'sudo apt install google-chrome-stable'.")
#     #
#     # CHROMEDRIVER_PATH = shutil.which("chromedriver")
#     # if not CHROMEDRIVER_PATH:
#     #     raise FileNotFoundError("ChromeDriver не найден! Установите его.")
#
#     # # Создаем уникальный путь для undetected_chromedriver
#     # uc_patcher_dir = f"/usr/src/app/chromedriver{process_id}"
#     # os.makedirs(uc_patcher_dir, exist_ok=True)
#
#     # Создаем уникальный путь для undetected_chromedriver
#     uc_patcher_dir = f"/root/git/afisha_bot/chromedriver{process_id}"
#     os.makedirs(uc_patcher_dir, exist_ok=True)
#
#     existing_driver = os.path.join(uc_patcher_dir, "chromedriver")
#
#
#     """Создает и настраивает Chrome для парсинга."""
#     options = uc.ChromeOptions()
#     options.add_argument(f"user-data-dir=/home/user/.config/google-chrome{process_id}")
#     options.add_argument("profile-directory=Default")
#
#     options.add_argument("--disable-blink-features=AutomationControlled")  # Убираем признак автоматизации
#     options.add_argument("--disable-gpu")  # Отключаем GPU, если сервер без графического интерфейса
#     options.add_argument("--no-sandbox")  # Запускаем без песочницы (нужно на серверах)
#     options.add_argument("--disable-dev-shm-usage")  # Избегаем проблем с разделяемой памятью (на Linux)
#     options.add_argument("--disable-infobars")  # Убираем "Chrome is being controlled by automated test software"
#     options.add_argument("--disable-popup-blocking")  # Отключаем блокировку всплывающих окон
#     options.add_argument("--remote-debugging-port=9222")  # Включаем удалённую отладку
#     options.add_argument("--start-maximized")  # Запуск в развернутом виде (некоторые сайты иначе ведут себя по-другому)
#     options.add_argument("--disable-extensions")  # Отключаем расширения, если они не нужны
#     options.add_argument("--disable-background-timer-throttling")  # Отключаем ограничение фоновых задач
#     options.add_argument("--disable-backgrounding-occluded-windows")  # Избегаем замедлений при работе в фоне
#     options.add_argument("--blink-settings=imagesEnabled=false")  # Отключаем загрузку изображений (ускорение парсинга)
#     options.add_argument("--mute-audio")  # Отключаем звук (если вдруг запускаются медиа)
#
#     # Подменяем user-agent (чтобы выглядел как обычный браузер)
#     options.add_argument(
#         "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
#     )
#
#     port = 9222 + process_id  # Разные порты для разных процессов
#
#
#     driver = uc.Chrome(options=options,
#                        driver_executable_path=existing_driver,
#                        port=port,
#                        use_subprocess=True)
#
#     logger.info(f"Инициализация драйвера...")
#
#     return driver

def init_driver():

    """Инициализация WebDriver с обработкой ошибок."""
    CHROME_PATH = shutil.which("google-chrome") or shutil.which("google-chrome-stable")
    if not CHROME_PATH:
        raise FileNotFoundError(
            "Google Chrome не найден! Установите его через 'sudo apt install google-chrome-stable'.")

    CHROMEDRIVER_PATH = shutil.which("chromedriver")
    if not CHROMEDRIVER_PATH:
        raise FileNotFoundError("ChromeDriver не найден! Установите его.")

    """Создает и настраивает Chrome для парсинга."""
    options = uc.ChromeOptions()
    options.add_argument("user-data-dir=/home/user/.config/google-chrome")
    options.add_argument("profile-directory=Default")

    options.add_argument("--disable-blink-features=AutomationControlled")  # Убираем признак автоматизации
    options.add_argument("--disable-gpu")  # Отключаем GPU, если сервер без графического интерфейса
    options.add_argument("--no-sandbox")  # Запускаем без песочницы (нужно на серверах)
    options.add_argument("--disable-dev-shm-usage")  # Избегаем проблем с разделяемой памятью (на Linux)
    options.add_argument("--disable-infobars")  # Убираем "Chrome is being controlled by automated test software"
    options.add_argument("--disable-popup-blocking")  # Отключаем блокировку всплывающих окон
    options.add_argument("--remote-debugging-port=9222")  # Включаем удалённую отладку
    options.add_argument("--start-maximized")  # Запуск в развернутом виде (некоторые сайты иначе ведут себя по-другому)
    options.add_argument("--disable-extensions")  # Отключаем расширения, если они не нужны
    options.add_argument("--disable-background-timer-throttling")  # Отключаем ограничение фоновых задач
    options.add_argument("--disable-backgrounding-occluded-windows")  # Избегаем замедлений при работе в фоне
    options.add_argument("--blink-settings=imagesEnabled=false")  # Отключаем загрузку изображений (ускорение парсинга)
    options.add_argument("--mute-audio")  # Отключаем звук (если вдруг запускаются медиа)

    # Подменяем user-agent (чтобы выглядел как обычный браузер)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    )

    driver = uc.Chrome(options=options,
                       use_subprocess=True)

    logger.info(f"Инициализация драйвера...")

    return driver

def get_event_description_yandex_afisha(list_of_links: List[str]) -> Dict[str, str] | None:
    """Получает описание мероприятия по ссылке."""

    descriptions = {url: 'Нет описания' for url in list_of_links}


    all_count = len(list_of_links)
    current_count = 1

    # 🖥 Запуск виртуального дисплея Xvfb (если вдруг не запущен)
    display_num = 99  # Разные Xvfb для каждого процесса
    os.system(f"Xvfb :{display_num} -screen 0 1920x1080x24 &")
    os.environ["DISPLAY"] = f":{display_num}"

    driver = init_driver()
    logger.info("🚀 Запускаем браузер...")

    try:
        for url, description in descriptions.items():
            log_memory_usage()

            attempts = 1
            max_attempts = 5

            while attempts < max_attempts:

                logger.info(f"[INFO] ℹ️  {current_count}/{all_count} Открываем страницу: {url}")
                driver.get(url)
                time.sleep(random.uniform(3, 6))

                scroll_down(driver)

                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                logger.info(f"[INFO] ℹ️  Страница загружена!")

                driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
                time.sleep(random.uniform(1, 2))

                driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 1.5);")
                time.sleep(random.uniform(1, 2))

                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 4))

                try:
                    # Проверяем наличие элемента с текстом "Ошибка 404" в error-page__body
                    error_body = driver.find_element(By.CSS_SELECTOR, "body.error-page__body")
                    error_text = error_body.find_element(By.CSS_SELECTOR, "div.ErrorTitle-wvicct-11").text

                    if "Ошибка 404" in error_text or "Такой страницы не существует" in error_text:
                        logger.warning(f"⚠️ Страница 404! Удаляем {url}")
                        asyncio.run(delete_event_by_url(url))
                        break

                except NoSuchElementException:
                    pass  # Ошибки нет, продолжаем

                try:
                    # Ждём появления блока описания на странице
                    description_block = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test-id='eventInfo.description']"))
                    )

                    soup = BeautifulSoup(description_block.get_attribute("innerHTML"), "html.parser")

                    # Пробуем найти текст описания внутри div class="tlWAxz"
                    description_element = soup.find("div", class_="tlWAxz")

                    if description_element:
                        new_description = description_element.text.strip()
                        logger.info(f"[INFO] ✅ Описание: {new_description}")

                        if len(new_description) > 5:
                            descriptions[url] = new_description
                        else:
                            logger.info(f"[INFO] ℹ️  Обнаруженное описание менее 5 символов. Установлено 'Нет описания'")

                    else:
                        logger.warning(f"⚠️ Описание не найдено.")
                        descriptions[url] = "Нет описания"

                    break

                except Exception as e:
                    attempts += 1
                    logger.error(f"[ERROR {attempts}/{max_attempts}] ❌ Ошибка при обработке {url}: {e}")

                    if attempts > 3:
                        asyncio.run(delete_event_by_url(url))
                        logger.warning(f"[WARNING] ⚠️ Страница {url} не загрузилась! Удаляем из базы.")
                        break

                    driver.quit()
                    time.sleep(5)
                    driver = init_driver()
                    logger.info(f'[INFO] ℹ️  Браузер перезапущен')
                    time.sleep(5)

            time.sleep(random.uniform(0.5, 2))  # Задержка для избежания бана
            current_count += 1
        logger.info(f'[INFO] ℹ️  Возвращение значений descriptions')
        return descriptions

    except Exception as e:
        logger.error(f"[ERROR] ❌ Произошла ошибка:")
        logger.error(traceback.format_exc())
        return descriptions

    finally:

        if 'driver' in locals():
            driver.quit()
            logger.info(f"[INFO] ℹ️  Браузер закрыт!")
