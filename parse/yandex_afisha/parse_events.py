import datetime
import os
import random
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

def scroll_down(driver):
    """Плавный скроллинг страницы для загрузки всех элементов"""
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollBy(0, window.innerHeight / 2);")  # Прокручиваем на 50% экрана
        time.sleep(random.uniform(1, 2))  # Ждём подгрузку элементов
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break  # Достигли конца страницы
        last_height = new_height

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

    # # Подменяем user-agent (чтобы выглядел как обычный браузер)
    # options.add_argument(
    #     "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    # )

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

    # 🔍 Проверка, что профиль работает
    driver.get("https://www.whatismybrowser.com/")

    # for link_of_type_event in create_base_urls():
    #     category_key = link_of_type_event.split('/')[-1].split('?')[0]
    #     category = types_of_event.get(category_key, 'Другое')
    #     attempt = 0
    #     max_attempts = 3
    #
    #     while attempt < max_attempts:
    #         try:
    #             events = []
    #             page = 1
    #
    #             while True:
    #                 url = link_of_type_event.format(today, page)
    #
    #                 logger.info(f"🔍 Парсим [{category}], страница {page}...")
    #                 driver.get(url)
    #                 time.sleep(random.uniform(3, 6))
    #
    #                 scroll_down(driver)
    #
    #                 WebDriverWait(driver, 10).until(
    #                     EC.presence_of_element_located((By.TAG_NAME, "body"))
    #                 )
    #                 driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
    #                 time.sleep(random.uniform(1, 2))
    #
    #                 driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 1.5);")
    #                 time.sleep(random.uniform(1, 2))
    #
    #                 driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    #                 time.sleep(random.uniform(2, 4))
    #
    #                 soup = BeautifulSoup(driver.page_source, "html.parser")
    #                 print(soup.text)  # Проверяем, какие реальные классы у элементов
    #
    #                 event_cards = soup.find_all("div", class_="event events-list__item yandex-sans")
    #                 if not event_cards:
    #                     logger.info("✅ Нет данных на странице, парсинг завершен.")
    #                     break
    #
    #                 for event in event_cards:
    #                     try:
    #                         title = event.find("h2", class_="Title-fq4hbj-3").text.strip()
    #                         date = event.find("li", class_="DetailsItem-fq4hbj-1").text.strip()
    #                         place = event.find("a", class_="PlaceLink-fq4hbj-2").text.strip()
    #                         link_tag = event.find("a", class_="EventLink-sc-1x07jll-2")
    #                         link = f"https://afisha.yandex.ru{link_tag['href']}" if link_tag else ""
    #
    #                         event_data = {
    #                             "title": title,
    #                             "category": category,
    #                             "date": date,
    #                             "venue": place,
    #                             "link": link,
    #                         }
    #
    #                         if title and date and place and link:
    #                             events.append(event_data)
    #
    #                     except AttributeError:
    #                         continue
    #
    #                 all_events.extend(events)
    #                 page += 1
    #                 time.sleep(1)  # Меньшая задержка для ускорения
    #
    #             break  # Успешно завершили категорию, выходим из while
    #         except Exception as e:
    #             attempt += 1
    #             logger.error(f"❌ Ошибка парсинга (попытка {attempt}/{max_attempts}): {e}")
    #             time.sleep(5)
    #
    #             driver.quit()  # Перезапуск браузера после ошибки
    #             driver = init_driver()
    #             logger.info("🔄 Перезапуск браузера...")

    driver.quit()
    return all_events

if __name__ == "__main__":
    results = get_all_events_yandex_afisha()
    if results:
        for event in results[:5]:  # Выводим первые 5 событий для проверки
            print(event)
