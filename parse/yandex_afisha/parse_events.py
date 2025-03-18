import datetime
import os
import shutil
import time
from typing import List, Dict
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc


from config import logger
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
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--profile-directory=Default")
    prefs = {
        "profile.managed_default_content_settings.images": 2,  # Выключаем загрузку картинок
        "profile.default_content_setting_values.notifications": 2,  # Выключаем всплывающие окна
        "profile.default_content_setting_values.geolocation": 2,  # Запрещаем геолокацию
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--blink-settings=imagesEnabled=false")  # Отключаем загрузку изображений
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")


    driver = uc.Chrome(options=options,
                       use_subprocess=True)

    logger.info(f"Инициализация драйвера...")

    return driver

def get_all_events_yandex_afisha() -> List[Dict]:
    all_events = []
    today = datetime.date.today()

    # 🖥 Запуск виртуального дисплея Xvfb (если вдруг не запущен)
    display_num = 99  # Разные Xvfb для каждого процесса
    os.system(f"Xvfb :{display_num} -screen 0 1920x1080x24 &")
    os.environ["DISPLAY"] = f":{display_num}"

    driver = init_driver()
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
                    logger.info(f'Пытаемся спарсить стр по адресу: {url}')
                    driver.get(url)
                    logger.info('driver.get')
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "event events-list__item yandex-sans"))
                    )
                    logger.info('webdriverwait')

                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    logger.info('soup')
                    event_cards = soup.find_all("div", class_="event events-list__item yandex-sans")
                    logger.info('event_cards')
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
                driver = init_driver()
                logger.info("🔄 Перезапуск браузера...")

    driver.quit()
    return all_events

if __name__ == "__main__":
    results = get_all_events_yandex_afisha()
    if results:
        for event in results[:5]:  # Выводим первые 5 событий для проверки
            print(event)
