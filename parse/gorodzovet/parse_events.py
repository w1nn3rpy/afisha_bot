# https://gorodzovet.ru/tomsk/
import datetime
import time
import shutil
from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from config import logger
from parse.common_funcs import normalize_category_gorodzovet

BASE_URL = 'https://gorodzovet.ru'

str_categories = {
    # Выставка
    'выставка': 'Выставка',
    'экспозиция': 'Выставка',
    'арт': 'Выставка',
    'галерея': 'Выставка',
    'инсталляция': 'Выставка',

    # Театр
    'спектакль': 'Театр',
    'сценка': 'Театр',
    'пьеса': 'Театр',
    'драма': 'Театр',
    'комедия': 'Театр',
    'трагедия': 'Театр',
    'моноспектакль': 'Театр',
    'театральный': 'Театр',

    # Для детей
    'детский': 'Для детей',
    'для детей': 'Для детей',
    'малыш': 'Для детей',
    'ребёнок': 'Для детей',
    'анимация': 'Для детей',
    'мультфильм': 'Для детей',
    'детям': 'Для детей',
    'семейный': 'Для детей',

    # Экскурсия
    'экскурсия': 'Экскурсия',
    'тур': 'Экскурсия',
    'прогулка': 'Экскурсия',
    'обзорная': 'Экскурсия',
    'поход': 'Экскурсия',
    'маршрут': 'Экскурсия',

    # Мастер-класс
    'мастер-класс': 'Мастер-класс',
    'мастеркласс': 'Мастер-класс',
    'обучение': 'Мастер-класс',
    'курс': 'Мастер-класс',
    'тренинг': 'Мастер-класс',
    'воркшоп': 'Мастер-класс',
    'занятие': 'Мастер-класс'
}


def get_links() -> List[str]:
    today = datetime.date.today()
    days = []

    for i in range(31):
        days.append(today + datetime.timedelta(days=i))

    urls = [f'https://gorodzovet.ru/tomsk/day{day}/' for day in days]

    return urls



def init_driver():
    """Инициализация WebDriver с обработкой ошибок."""
    CHROME_PATH = shutil.which("google-chrome") or shutil.which("google-chrome-stable")
    if not CHROME_PATH:
        raise FileNotFoundError(
            "Google Chrome не найден! Установите его через 'sudo apt install google-chrome-stable'.")

    CHROMEDRIVER_PATH = shutil.which("chromedriver")
    if not CHROMEDRIVER_PATH:
        raise FileNotFoundError("ChromeDriver не найден! Установите его.")

    chrome_options = Options()
    chrome_options.binary_location = CHROME_PATH
    chrome_options.add_argument("--headless")  # Без GUI
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def get_all_events_gorodzovet(urls: List[str]) -> List[dict] | None:
    """Парсинг всех мероприятий с Афиши с защитой от крашей."""
    attempt = 0
    max_attempts = 3
    while attempt < max_attempts:
        try:
            driver = init_driver()
            logger.info("🚀 Запускаем браузер...")

            events = []
            for url in urls:
                logger.info(f"Найдено мероприятий: {len(events)}\n🔍 Парсим страницу {url}...")

                driver.get(url)
                time.sleep(2)  # Ожидание загрузки страницы
                soup = BeautifulSoup(driver.page_source, "html.parser")

                page_events = []
                event_blocks = soup.find_all("div", class_="event-block")

                if not event_blocks:
                    logger.info("✅ Нет данных на странице, парсинг завершен.")
                    break

                for event in event_blocks:
                    title_tag = event.find("h3", class_="lines lines2")
                    category_tags = event.find("div", class_="event-tags")
                    date_venue_tag = event.find("span", class_="event-day innlink")
                    href_tag = event.find("div", class_="innlink event-link save-click")

                    if not title_tag or not date_venue_tag:
                        logger.error('SKIP')
                        continue  # Если нет данных, пропускаем

                    title = title_tag.text.strip()
                    event_link = f"https://www.gorodzovet.ru{href_tag['data-link']}"
                    category = ''
                    try:
                        for word in title.split():
                            if word.lower() in str_categories:
                                category = str_categories.get(word.lower())
                                break
                            else:
                                category = normalize_category_gorodzovet(category_tags.text.strip()) if category_tags else "Другое"
                    except Exception as e:
                        logger.error(f'ОШИБКА: {e}')

                    date = datetime.datetime.strptime(date_venue_tag['data-link'].split("day")[-1].strip("/"), "%Y/%m/%d").date()

                    event_data = {
                        "title": title,
                        "date": date,
                        "category": category,
                        "venue": "Неизвестно",
                        "link": event_link,
                    }
                    logger.info(f'Событие: {title}\n'
                                f'Дата: {date}\n'
                                f'Категория: {category}\n'
                                f'Ссылка: {href_tag["data-link"]}\n')

                    if date and title and category and event_link:
                        page_events.append(event_data)

                events.extend(page_events)
                time.sleep(2)  # Пауза перед переходом на следующую страницу

            driver.quit()
            return events

        except Exception as e:
            attempt += 1
            logger.error(f"❌ Ошибка парсинга (попытка {attempt}/{max_attempts}): {e}")
            time.sleep(5)  # Ожидание перед повторной попыткой

            if 'driver' in locals():
                driver.quit()  # Закрываем перед новым запуском
                logger.info("🔄 Перезапуск браузера...")

    return events
