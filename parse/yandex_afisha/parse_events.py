import datetime
import time
from typing import List, Dict
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import logger
from parse.ticketland.parse_description_of_events import init_driver
def create_base_urls():
    categories = ["concert", "theatre", "kids", "art", "standup", "excursions", "show", "quest", "masterclass", "lectures"]
    base_urls = [f"https://afisha.yandex.ru/tomsk/{cat}?source=menu&date={{}}&period=365&page={{}}" for cat in categories]
    return base_urls

types_of_event = {
    "concert": "Концерт",
    "theatre": "Театр",
    "kids": "Для детей",
    "art": "Выставка",
    "standup": "Другое",
    "excursions": "Экскурсия",
    "show": "Другое",
    "quest": "Другое",
    "masterclass": "Мастер-класс",
    "lectures": "Наука"
}

def get_all_events_yandex_afisha() -> List[Dict]:
    all_events = []
    today = datetime.date.today()

    driver = init_driver(1)
    logger.info("🚀 Запускаем браузер...")

    for link_of_type_event in create_base_urls():
        category_key = link_of_type_event.split('/')[-1].split('?')[0]
        category = types_of_event.get(category_key, 'Другое')
        attempt = 0
        max_attempts = 3

        while attempt < max_attempts:
            try:
                events = []
                page = 1

                while True:
                    url = link_of_type_event.format(today, page)

                    logger.info(f"🔍 Парсим [{category}], страница {page}...")
                    logger.debug(f'Пытаемся спарсить стр по адресу: {url}')
                    driver.get(url)
                    logger.debug('driver.get')
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "event events-list__item yandex-sans"))
                    )
                    logger.debug('webdriverwait')

                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    logger.debug('soup')
                    event_cards = soup.find_all("div", class_="event events-list__item yandex-sans")
                    logger.debug('event_cards')
                    if not event_cards:
                        logger.info("✅ Нет данных на странице, парсинг завершен.")
                        break

                    for event in event_cards:
                        try:
                            title = event.find("h2", class_="Title-fq4hbj-3").text.strip()
                            date = event.find("li", class_="DetailsItem-fq4hbj-1").text.strip()
                            place = event.find("a", class_="PlaceLink-fq4hbj-2").text.strip()
                            link_tag = event.find("a", class_="EventLink-sc-1x07jll-2")
                            link = f"https://afisha.yandex.ru{link_tag['href']}" if link_tag else ""

                            event_data = {
                                "title": title,
                                "category": category,
                                "date": date,
                                "venue": place,
                                "link": link,
                            }

                            if title and date and place and link:
                                events.append(event_data)

                        except AttributeError:
                            continue

                    all_events.extend(events)
                    page += 1
                    time.sleep(1)  # Меньшая задержка для ускорения

                break  # Успешно завершили категорию, выходим из while
            except Exception as e:
                attempt += 1
                logger.error(f"❌ Ошибка парсинга (попытка {attempt}/{max_attempts}): {e}")
                time.sleep(5)

                driver.quit()  # Перезапуск браузера после ошибки
                driver = init_driver(1)
                logger.info("🔄 Перезапуск браузера...")

    driver.quit()
    return all_events

if __name__ == "__main__":
    results = get_all_events_yandex_afisha()
    if results:
        for event in results[:5]:  # Выводим первые 5 событий для проверки
            print(event)
