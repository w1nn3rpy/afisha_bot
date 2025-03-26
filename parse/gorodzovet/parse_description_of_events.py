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
from database.events_db import delete_event_by_url, add_venue
from parse.afisharu.parse_events import init_driver
from parse.common_funcs import log_memory_usage

def extract_description(soup: BeautifulSoup) -> str:
    desc_block = soup.select_one("div.eventText div.container--padding")
    if not desc_block:
        return "Описание не найдено"

    # Попробуем найти первый <p>
    first_p = desc_block.find("p")
    if first_p:
        return first_p.get_text(strip=True)

    # Если <p> нет — берём всё содержимое до первого <br>
    raw_html = str(desc_block)
    parts = raw_html.split("<br")
    if parts:
        first_part = BeautifulSoup(parts[0], "html.parser").get_text(strip=True)
        return first_part

    return desc_block.get_text(strip=True)

def get_event_description_gorodzovet(process_id, list_of_links: List[str]) -> Dict[str, str] | None:
    """Получает описание мероприятия по ссылке."""

    descriptions = {url: 'Нет описания' for url in list_of_links}


    all_count = len(list_of_links)
    current_count = 1

    driver = init_driver()
    try:
        for url, description in descriptions.items():
            log_memory_usage()

            attempts = 1
            max_attempts = 5

            while attempts < max_attempts:

                logger.info(f"[{process_id}] [INFO] ℹ️  {current_count}/{all_count} Открываем страницу: {url}")
                driver.get(url)
                body = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                logger.info(f"[{process_id}] [INFO] ℹ️  Страница загружена!")

                try:
                    # Ждём появления блока описания
                    soup = BeautifulSoup(body.get_attribute("innerHTML"), "html.parser")
                    try:
                        # Пробуем найти основной текст внутри RESTRICT-TEXT
                        get_description = extract_description(soup)

                        if get_description:
                            new_description = get_description
                            logger.info(f"[{process_id}] [INFO] ✅ Описание: {new_description}")

                            if len(new_description) > 5:
                                descriptions[url] = new_description
                                break
                            else:
                                logger.info(f"[{process_id}] [INFO] ℹ️  Обнаруженное описание менее 5 символов. Установлено 'Нет описания'")
                                break
                    except Exception as e:
                        logger.warning(f"[{process_id}] ⚠️ Ошибка при парсинге описания: {e}")

                    try:
                        venue_div = soup.find("div", class_="seance-venue-name")

                        if venue_div:
                            venue = venue_div.get_text(strip=True)
                            asyncio.to_thread(add_venue, venue, url)
                    except Exception as e:
                        logger.warning(f"[{process_id}] ⚠️ Ошибка при парсинге venue: {e}")

                except Exception as e:
                    attempts += 1
                    logger.error(f"[{process_id}] [ERROR {attempts}/{max_attempts}] ❌ Ошибка при обработке {url}: {e}")

                    if attempts > 3:
                        asyncio.run(delete_event_by_url(url))
                        logger.warning(f"[{process_id}] [WARNING] ⚠️ Страница {url} не загрузилась! Удаляем из базы.")
                        break

                    driver.quit()
                    time.sleep(5)
                    driver = init_driver()
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
