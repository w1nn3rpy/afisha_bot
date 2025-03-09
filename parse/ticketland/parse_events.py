
# sudo apt update && sudo apt install -y google-chrome-stable
# wget "https://storage.googleapis.com/chrome-for-testing-public/133.0.6943.126/linux64/chromedriver-linux64.zip"
# unzip chromedriver-linux64.zip
# sudo mv chromedriver /usr/bin/chromedriver
# sudo chmod +x /usr/bin/chromedriver

import re
from tempfile import mkdtemp
from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import shutil

from config import logger

BASE_URL = "https://tomsk.ticketland.ru/search/performance/"



def clean_date(date_text):
    """
    Очищает дату от лишних символов и приводит к формату: '10 окт' и '20:00'
    """

    months_dict = {'янв': 'января',
                   'фев': 'февраля',
                   'мар': 'марта',
                   'апр': 'апреля',
                   'мая': 'мая',
                   'июн': 'июня',
                   'июл': 'июля',
                   'авг': 'августа',
                   'сен': 'сентября',
                   'окт': 'октября',
                   'ноя': 'ноября',
                   'дек': 'декабря'}

    date_text = date_text.replace("\xa0", " ")  # Убираем неразрывные пробелы
    match = re.search(r"(\d{1,2} \w+)•\w+•(\d{2}:\d{2})", date_text)

    if match:
        date_part = match.group(1)  # "10 окт"
        date_part = date_part.split()[0] + ' ' + months_dict.get(date_part.split()[1])
        return date_part
    return "Неизвестно"


def get_all_events_ticketland() -> List[dict] | None:
    # Проверяем наличие Google Chrome
    CHROME_PATH = shutil.which("google-chrome") or shutil.which("google-chrome-stable")
    if not CHROME_PATH:
        raise FileNotFoundError(
            "Google Chrome не найден! Установите его через 'sudo apt install google-chrome-stable'.")

    # Проверяем наличие ChromeDriver
    CHROMEDRIVER_PATH = shutil.which("chromedriver")
    if not CHROMEDRIVER_PATH:
        raise FileNotFoundError("ChromeDriver не найден! Установите его.")

    # Настройки Selenium
    chrome_options = Options()
    chrome_options.binary_location = CHROME_PATH
    chrome_options.add_argument("--headless")  # Без GUI
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    try:
        logger.info("🚀 Запускаем браузер...")
        service = Service(CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        events = []

        page = 1
        while True:
            url = f"{BASE_URL}?sort=date&so=desc&page={page}"
            logger.info(f"Найдено мероприятий: {len(events)}\n🔍 Парсим страницу {page}...")

            driver.get(url)
            soup = BeautifulSoup(driver.page_source, "html.parser")

            page_events = []
            for event in soup.find_all("div", class_="card-search"):
                title_tag = event.find("a", class_="card-search__name")
                date_tag = event.find("a", class_="text-uppercase")
                category_tag = event.select_one("p[class^='card-search__category']")
                venue_tag = event.find("a", attrs={"data-click-target": "ploshadka"})  # Место проведения

                if title_tag and date_tag:
                    title = title_tag.text.strip()
                    event_link = f"https://tomsk.ticketland.ru{title_tag['href']}"

                    for span in date_tag.find_all("span", class_="card__search__amount d-none d-lg-inline-block"):
                        span.decompose()

                    raw_date = date_tag.text.strip()
                    date = clean_date(raw_date)  # Преобразуем дату и время

                    category = category_tag.text.strip() if category_tag else "Неизвестно"  # Тип мероприятия
                    venue = venue_tag["title"].strip() if venue_tag else "Неизвестно"

                    event_data = {
                        "title": title,
                        "date": date,
                        "category": category,
                        "venue": venue,  # Добавлено место проведения
                        "link": event_link,
                    }
                    page_events.append(event_data)

            if not page_events:
                logger.info("✅ Нет данных на странице, парсинг завершен.")
                break

            events.extend(page_events)
            page += 1
            time.sleep(2)

        driver.quit()
        return events

    except Exception as e:
        logger.error(f"❌ Ошибка парсинга: {e}")
        return None

    finally:
        if 'driver' in locals():
            driver.quit()
        logger.info("🛑 Браузер закрыт.")


if __name__ == "__main__":
    results = get_all_events_ticketland()
    if results:
        for event in results[:5]:  # Выводим первые 5 событий для проверки
            print(event)

# результат
# {
# 'title': 'Группа «Neverlove»',
# 'date': '12 мая',
# 'time': '19:00',
# 'category': 'Концерты',
# 'venue': 'Клуб «Маяк»',
# 'link': 'https://tomsk.ticketland.ru/kluby/klub-vk-stadium/neverlove/'
# }