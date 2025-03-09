import asyncio
import random
import time
import traceback
from typing import List, Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from config import logger
from database.events_db import delete_event_by_url
from parse.afisharu.parse_events import init_driver


def get_event_description_afisharu(process_id, list_of_links: List[str]) -> Dict[str, str] | None:
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
