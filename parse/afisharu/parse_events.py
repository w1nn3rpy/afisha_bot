# https://www.afisha.ru/tomsk/events/performances/exhibitions/concerts/

import re
import time
import shutil
from typing import List
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from config import logger

BASE_URL = "https://www.afisha.ru/tomsk/events/page{}/performances/exhibitions/concerts/"


def get_all_events_afisharu() -> List[dict] | None:
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
            url = BASE_URL.format(page)
            logger.info(f"Найдено мероприятий: {len(events)}\n🔍 Парсим страницу {page}...")

            driver.get(url)
            soup = BeautifulSoup(driver.page_source, "html.parser")

            page_events = []
            for event in soup.find_all("div", class_="oP17O"):
                title_tag = event.find("a", class_="CjnHd y8A5E nbCNS yknrM")
                category_tag = event.find("div", class_="S_wwn")
                date_venue_tag = event.find("div", class_="_JP4u")
                link_tag = event.find("a", class_="CjnHd y8A5E Vrui1")

                if title_tag and date_venue_tag:
                    title = title_tag.text.strip()
                    event_link = f"https://www.afisha.ru{title_tag['href']}"
                    category = category_tag.text.strip() if category_tag else "Неизвестно"
                    date_venue_text = date_venue_tag.text.strip()

                    # Разделение даты и места проведения
                    date_venue_split = date_venue_text.split(", ")
                    date = date_venue_split[0] if len(date_venue_split) > 0 else "Неизвестно"
                    venue = date_venue_split[1] if len(date_venue_split) > 1 else "Неизвестно"

                    event_data = {
                        "title": title,
                        "date": date,
                        "category": category,
                        "venue": venue,
                        "link": event_link,
                    }
                    page_events.append(event_data)

            if not page_events:
                logger.info("✅ Нет данных на странице, парсинг завершен.")
                break

            events.extend(page_events)
            page += 1
            time.sleep(2)

        return events

    except Exception as e:
        logger.error(f"❌ Ошибка парсинга: {e}")
        return None

    finally:
        if 'driver' in locals():
            driver.quit()
        logger.info("🛑 Браузер закрыт.")


if __name__ == "__main__":
    results = get_all_events_afisharu()
    if results:
        for event in results[:5]:  # Выводим первые 5 событий для проверки
            print(event)
