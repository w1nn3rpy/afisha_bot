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

def init_driver():
    """Инициализация WebDriver с обработкой ошибок."""
    CHROME_PATH = shutil.which("google-chrome") or shutil.which("google-chrome-stable")
    if not CHROME_PATH:
        raise FileNotFoundError("Google Chrome не найден! Установите его через 'sudo apt install google-chrome-stable'.")

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
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--memory-pressure-off")
    chrome_options.add_argument("--renderer-process-limit=2")  # Ограничение рендер-процессов
    chrome_options.add_argument("--max-old-space-size=512")  # Ограничение памяти

    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def get_all_events_afisharu() -> List[dict] | None:
    """Парсинг всех мероприятий с Афиши с защитой от крашей."""
    attempt = 0
    max_attempts = 3

    while attempt < max_attempts:
        try:
            driver = init_driver()
            logger.info("🚀 Запускаем браузер...")

            events = []
            page = 1

            while True:
                url = BASE_URL.format(page)
                logger.info(f"Найдено мероприятий: {len(events)}\n🔍 Парсим страницу {page}...")

                driver.get(url)
                time.sleep(2)  # Ожидание загрузки страницы
                soup = BeautifulSoup(driver.page_source, "html.parser")

                page_events = []
                event_blocks = soup.find_all("div", class_="oP17O")

                if not event_blocks:
                    logger.info("✅ Нет данных на странице, парсинг завершен.")
                    break

                for event in event_blocks:
                    title_tag = event.find("a", class_="CjnHd y8A5E nbCNS yknrM")
                    category_tag = event.find("div", class_="S_wwn")
                    date_venue_tag = event.find("div", class_="_JP4u")

                    if not title_tag or not date_venue_tag:
                        continue  # Если нет данных, пропускаем

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

                events.extend(page_events)
                page += 1
                time.sleep(2)  # Пауза перед переходом на следующую страницу

            driver.quit()
            return events

        except Exception as e:
            logger.error(f"❌ Ошибка парсинга (попытка {attempt+1}/{max_attempts}): {e}")
            attempt += 1
            time.sleep(5)  # Ожидание перед повторной попыткой

            if 'driver' in locals():
                driver.quit()  # Закрываем перед новым запуском
                logger.info("🔄 Перезапуск браузера...")

    return None  # Если после всех попыток не удалось спарсить

if __name__ == "__main__":
    results = get_all_events_afisharu()
    if results:
        for event in results[:5]:  # Выводим первые 5 событий для проверки
            print(event)



# [{'title': 'Подыскиваю жену, недорого!', 'date': '15 марта', 'category': 'Комедия', 'venue': 'Томский драматический театр', 'link': 'https://www.afisha.ru/performance/podyskivayu-zhenu-nedorogo-85589/'}, {'title': 'Звери', 'date': '16 марта в 19:00', 'category': 'Рок', 'venue': 'Дворец зрелищ и спорта', 'link': 'https://www.afisha.ru/concert/zveri-2282055/'}, {'title': 'Мастер-класс «Секреты глины: горшочек для меда с обжигом»', 'date': 'до 24 апреля', 'category': 'Мастер-классы', 'venue': 'Дворец народного творчества «Авангард»', 'link': 'https://www.afisha.ru/exhibition/master-klass-sekrety-gliny-gorshochek-dlya-meda-s-obzhigom-316676/'}, {'title': 'Чужих мужей не бывает', 'date': '6 апреля в 19:00', 'category': 'Комедия', 'venue': 'Томский драматический театр', 'link': 'https://www.afisha.ru/performance/chuzhih-muzhey-ne-byvaet-201745/'}, {'title': 'Шоу Иллюзии XXI века', 'date': '8 марта', 'category': 'Детский', 'venue': 'Версия', 'link': 'https://www.afisha.ru/performance/shou-illyuzii-xxi-veka-1000081/'}, {'title': 'Комната культуры', 'date': '15 марта в 20:00', 'category': 'Поп', 'venue': 'Face Club', 'link': 'https://www.afisha.ru/concert/komnata-kultury-2234979/'}, {'title': 'Мастер-класс «Искусство обжига: создаем бокал своей мечты»', 'date': 'до 24 апреля', 'category': 'Мастер-классы', 'venue': 'Дворец народного творчества «Авангард»', 'link': 'https://www.afisha.ru/exhibition/master-klass-iskusstvo-obzhiga-sozdaem-bokal-svoey-mechty-316677/'}, {'title': 'Цветы для Элджернона', 'date': '28 и 29 марта', 'category': 'Драматический', 'venue': 'Дворец народного творчества «Авангард»', 'link': 'https://www.afisha.ru/performance/cvety-dlya-eldzhernona-277604/'}, {'title': 'Ольга Малащенко', 'date': '18 мая в 19:00', 'category': 'Юмор', 'venue': 'ЦК ТГУ', 'link': 'https://www.afisha.ru/concert/olga-malashchenko-2269788/'}, {'title': 'Один на один: Пикник', 'date': '22 апреля в 19:00', 'category': 'Рок', 'venue': 'Томская филармония', 'link': 'https://www.afisha.ru/concert/odin-na-odin-piknik-2274850/'}, {'title': 'Дискотека «Все хиты»', 'date': '26 марта в 19:00', 'category': 'Поп', 'venue': 'Дворец зрелищ и спорта', 'link': 'https://www.afisha.ru/concert/diskoteka-vse-hity-2278557/'}, {'title': 'Перевоплотиться: Zoloto', 'date': '18 марта в 19:00', 'category': 'Поп', 'venue': 'Face Club', 'link': 'https://www.afisha.ru/concert/perevoplotitsya-zoloto-2279940/'}, {'title': 'Егор Крид', 'date': '16 апреля в 20:00', 'category': 'Поп', 'venue': 'Дворец зрелищ и спорта', 'link': 'https://www.afisha.ru/concert/egor-krid-2227432/'},
# {'title': 'Богемская рапсодия: Radio Queen с симфоническим оркестром', 'date': '22 марта в 18:00', 'category': 'Рок', 'venue': 'ЦК ТГУ', 'link': 'https://www.afisha.ru/concert/bogemskaya-rapsodiya-radio-queen-s-simfonicheskim-orkestrom-2164937/'}, {'title': 'Нидаль Абу-Газале', 'date': '10 июня в 19:00', 'category': 'Юмор', 'venue': 'ЦК ТГУ', 'link': 'https://www.afisha.ru/concert/nidal-abu-gazale-2292349/'}, {'title': 'Neverlove', 'date': '12 мая в 19:00', 'category': 'Рок', 'venue': 'Маяк', 'link': 'https://www.afisha.ru/concert/neverlove-2297139/'}, {'title': 'Группа Стаса Намина «Цветы»', 'date': '10 марта в 19:00', 'category': 'Рок', 'venue': 'Томская филармония', 'link': 'https://www.afisha.ru/concert/gruppa-stasa-namina-cvety-2231576/'}, {'title': 'Горшенев', 'date': '16 марта в 19:00', 'category': 'Рок', 'venue': 'Томская филармония', 'link': 'https://www.afisha.ru/concert/gorshenev-2270906/'}, {'title': 'DS Crew', 'date': '1 апреля в 19:00', 'category': 'Неизвестно', 'venue': 'Томский драматический театр', 'link': 'https://www.afisha.ru/concert/ds-crew-2281908/'}, {'title': 'Слот', 'date': '28 марта в 19:00', 'category': 'Рок', 'venue': 'Face Club', 'link': 'https://www.afisha.ru/concert/slot-2231920/'}, {'title': 'Магия Севера: Олена Уутай', 'date': '17 апреля в 19:00', 'category': 'Этно', 'venue': 'ЦК ТГУ', 'link': 'https://www.afisha.ru/concert/magiya-severa-olena-uutay-2218963/'}, {'title': 'Папин Олимпос', 'date': '10 марта в 19:00', 'category': 'Рок', 'venue': 'Face Club', 'link': 'https://www.afisha.ru/concert/papin-olimpos-2296689/'}, {'title': 'Ангел и Демон: Княzz', 'date': '11 апреля в 19:00', 'category': 'Рок', 'venue': 'Дворец зрелищ и спорта', 'link': 'https://www.afisha.ru/concert/angel-i-demon-knyazz-2278833/'}, {'title': 'Паша Техник', 'date': '6 апреля в 20:00', 'category': 'Хип-хоп', 'venue': 'Face Club', 'link': 'https://www.afisha.ru/concert/pasha-tehnik-2294194/'}, {'title': 'Варвара Щербакова', 'date': '8 апреля в 19:00', 'category': 'Юмор', 'venue': 'Томская филармония', 'link': 'https://www.afisha.ru/concert/varvara-shcherbakova-2248780/'}, {'title': 'Pussykiller', 'date': '26 апреля в 20:00', 'category': 'Хип-хоп', 'venue': 'Face Club', 'link': 'https://www.afisha.ru/concert/pussykiller-2296773/'}, {'title': 'Сова', 'date': '13 июня в 20:00', 'category': 'Поп', 'venue': 'Капитал', 'link': 'https://www.afisha.ru/concert/sova-2296643/'},
# {'title': 'Макулатура', 'date': '14 марта в 19:00', 'category': 'Хип-хоп', 'venue': 'Make Love Pizza', 'link': 'https://www.afisha.ru/concert/makulatura-2294602/'}, {'title': 'Танцевальные вечера для людей «элегантного возраста»', 'date': '12', 'category': 'Эстрада', 'venue': '19 и 26 марта', 'link': 'https://www.afisha.ru/concert/tancevalnye-vechera-dlya-lyudiy-elegantnogo-vozrasta-2222978/'}, {'title': 'Лариса Долина. Лучшее. Любимое', 'date': '24 марта в 19:00', 'category': 'Джаз', 'venue': 'Томская филармония', 'link': 'https://www.afisha.ru/concert/larisa-dolina-luchshee-lyubimoe-2266697/'}, {'title': 'Madk1d', 'date': '30 марта в 20:00', 'category': 'Хип-хоп', 'venue': 'Face Club', 'link': 'https://www.afisha.ru/concert/madk1d-2296479/'}, {'title': 'Шары', 'date': '12 марта в 19:00', 'category': 'Рок', 'venue': 'Santa Monica', 'link': 'https://www.afisha.ru/concert/shary-2297216/'}, {'title': 'Вечер шансона: Эдуард Хуснутдинов', 'date': '23 марта в 20:00', 'category': 'Шансон', 'venue': 'Face Club', 'link': 'https://www.afisha.ru/concert/vecher-shansona-eduard-husnutdinov-2294535/'}, {'title': 'Fortuna812 и Юпи', 'date': '6 марта в 19:00', 'category': 'Хип-хоп', 'venue': 'Face Club', 'link': 'https://www.afisha.ru/concert/fortuna812-i-yupi-2281911/'}, {'title': 'Standup шоу ТНТ', 'date': '27 марта в 19:00', 'category': 'Юмор', 'venue': 'ЦК ТГУ', 'link': 'https://www.afisha.ru/concert/standup-shou-tnt-2268105/'}, {'title': 'Литературный вечер. Одиссея мужчин среднего возраста: Александр Бессонов', 'date': '19 апреля в 15:00', 'category': 'Литература', 'venue': 'Версия', 'link': 'https://www.afisha.ru/concert/literaturniy-vecher-odisseya-muzhchin-srednego-vozrasta-aleksandr-bessonov-2297463/'}, {'title': 'Зомб', 'date': '17 октября в 20:00', 'category': 'Хип-хоп', 'venue': 'Face Club', 'link': 'https://www.afisha.ru/concert/zomb-2280301/'}, {'title': 'NTL', 'date': '18 апреля в 21:00', 'category': 'Рок', 'venue': 'Капитал', 'link': 'https://www.afisha.ru/concert/ntl-2297970/'}, {'title': 'Б.А.У.', 'date': '17 мая в 19:00', 'category': 'Тяжелый рок', 'venue': 'Варяг', 'link': 'https://www.afisha.ru/concert/b-a-u-2296288/'}, {'title': 'Polly Jane', 'date': '8 марта в 19:00', 'category': 'Джаз', 'venue': 'Underground', 'link': 'https://www.afisha.ru/concert/polly-jane-2297262/'}, {'title': 'Константин Кулясов', 'date': '12 июня в 20:00', 'category': 'Рок', 'venue': 'Варяг', 'link': 'https://www.afisha.ru/concert/konstantin-kulyasov-2295171/'}, {'title': 'Алиса Дударева', 'date': '15 мая в 20:00', 'category': 'Юмор', 'venue': 'Santa Monica', 'link': 'https://www.afisha.ru/concert/alisa-dudareva-6000138/'},
# {'title': 'Юбилейный концерт Владимира Морозова', 'date': '18 апреля в 19:00', 'category': 'Эстрада', 'venue': 'Дворец народного творчества «Авангард»', 'link': 'https://www.afisha.ru/concert/yubileyniy-koncert-vladimira-morozova-2296546/'}, {'title': 'Ravanna', 'date': '10 октября в 20:00', 'category': 'Рок', 'venue': 'Варяг', 'link': 'https://www.afisha.ru/concert/ravanna-2292826/'}, {'title': 'Cold Blooded Murder', 'date': '13 апреля в 19:00', 'category': 'Тяжелый рок', 'venue': 'Варяг', 'link': 'https://www.afisha.ru/concert/cold-blooded-murder-2296906/'}, {'title': 'Василий Уриевский', 'date': '26 марта в 19:00', 'category': 'Авторская песня', 'venue': 'Underground', 'link': 'https://www.afisha.ru/concert/vasiliy-urievskiy-2295940/'}, {'title': 'БО...', 'date': '7 марта в 21:00', 'category': 'Рок', 'venue': 'Варяг', 'link': 'https://www.afisha.ru/concert/bo-2298506/'}, {'title': 'Анхель Онтальва', 'date': '12 апреля в 19:00', 'category': 'Джаз', 'venue': 'Underground', 'link': 'https://www.afisha.ru/concert/anhel-ontalva-6000404/'}, {'title': 'Павел Пиковский и Хьюго', 'date': '15 апреля в 20:00', 'category': 'Авторская песня', 'venue': 'Santa Monica', 'link': 'https://www.afisha.ru/concert/pavel-pikovskiy-i-hyugo-2295230/'}, {'title': 'Vomitous Mass', 'date': '6 декабря', 'category': 'Тяжелый рок', 'venue': 'Варяг', 'link': 'https://www.afisha.ru/concert/vomitous-mass-2294792/'}, {'title': 'Влом!', 'date': '15 марта в 20:00', 'category': 'Рок', 'venue': 'Варяг', 'link': 'https://www.afisha.ru/concert/vlom-2292574/'}, {'title': 'Элизабет Аттим Аллаи и квартет Александра Рождественского', 'date': '29 марта в 19:00', 'category': 'Джаз', 'venue': 'Underground', 'link': 'https://www.afisha.ru/concert/elizabet-attim-allai-i-kvartet-aleksandra-rozhdestvenskogo-2297266/'}, {'title': 'Квинтет Андрея Турыгина', 'date': '26 апреля в 19:00', 'category': 'Джаз', 'venue': 'Underground', 'link': 'https://www.afisha.ru/concert/kvintet-andreya-turygina-6000415/'}, {'title': 'Ани Лорак', 'date': '15 мая в 19:00', 'category': 'Поп', 'venue': 'Дворец зрелищ и спорта', 'link': 'https://www.afisha.ru/concert/ani-lorak-6000735/'}, {'title': 'Мастер-класс по изготовлению глиняной тарелки', 'date': 'с 7 марта', 'category': 'Мастер-классы', 'venue': 'Дворец народного творчества «Авангард»', 'link': 'https://www.afisha.ru/exhibition/master-klass-po-izgotovleniyu-glinyanoy-tarelki-305109/'}, {'title': 'Мастер-класс по гончарному мастерству «Стакан»', 'date': 'с 14 марта', 'category': 'Мастер-классы', 'venue': 'Дворец народного творчества «Авангард»', 'link': 'https://www.afisha.ru/exhibition/master-klass-po-goncharnomu-masterstvu-stakan-305110/'},
# {'title': 'Мастер-класс «Изготовление глиняной вазы»', 'date': 'с 21 марта', 'category': 'Мастер-классы', 'venue': 'Дворец народного творчества «Авангард»', 'link': 'https://www.afisha.ru/exhibition/master-klass-izgotovlenie-glinyanoy-vazy-305111/'}, {'title': 'Мы едем, едем, едем...', 'date': '29 марта в 15:00', 'category': 'Детский', 'venue': 'Гостевая «Белозерье»', 'link': 'https://www.afisha.ru/performance/my-edem-edem-edem-312652/'}, {'title': 'Приключения Буратино', 'date': '12 апреля в 15:00', 'category': 'Детский', 'venue': 'Гостевая «Белозерье»', 'link': 'https://www.afisha.ru/performance/priklyucheniya-buratino-312653/'}, {'title': 'Сказка о потерянном времени', 'date': '26 апреля в 15:00', 'category': 'Детский', 'venue': 'Гостевая «Белозерье»', 'link': 'https://www.afisha.ru/performance/skazka-o-poteryannom-vremeni-312654/'}, {'title': 'Царь обезьян', 'date': '15 марта в 15:00', 'category': 'Детский', 'venue': 'Гостевая «Белозерье»', 'link': 'https://www.afisha.ru/performance/car-obezyan-312655/'}, {'title': 'Виртуальная экскурсия «Кремль. Живая история Российской державы»', 'date': 'с 31 марта', 'category': 'Экскурсии', 'venue': 'Дворец народного творчества «Авангард»', 'link': 'https://www.afisha.ru/exhibition/virtualnaya-ekskursiya-kreml-zhivaya-istoriya-rossiyskoy-derzhavy-316438/'}, {'title': 'Познавательная программа «Молодецкие забавы»', 'date': 'с 19 марта', 'category': 'Интерактивная', 'venue': 'ДК «Восток»', 'link': 'https://www.afisha.ru/exhibition/poznavatelnaya-programma-molodeckie-zabavy-1000154/'}, {'title': 'Интеллектуальная программа «Назад в прошлое»', 'date': 'с 22 марта', 'category': 'Интерактивная', 'venue': 'ДК «Восток»', 'link': 'https://www.afisha.ru/exhibition/intellektualnaya-programma-nazad-v-proshloe-1000246/'}, {'title': '22 сезон: Гузель Уразова', 'date': '13 апреля в 18:00', 'category': 'Эстрада', 'venue': 'Дворец искусств «Современник»', 'link': 'https://www.afisha.ru/concert/22-sezon-guzel-urazova-2281706/'}, {'title': 'В ритме музыки', 'date': '14 и 28 марта', 'category': 'Эстрада', 'venue': 'ДК «Восток»', 'link': 'https://www.afisha.ru/concert/v-ritme-muzyki-2297387/'}, {'title': 'Песни нашей России', 'date': '16 марта в 18:00', 'category': 'Эстрада', 'venue': 'ДК «Восток»', 'link': 'https://www.afisha.ru/concert/pesni-nashey-rossii-6000654/'}]