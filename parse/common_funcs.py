import psutil

from config import logger

CATEGORY_MAPPING = {
    "концерты": "Концерт",
    "классика": "Концерт",
    "рок": "Концерт",
    "тяжелый рок": "Концерт",
    "поп": "Концерт",
    "джаз": "Концерт",
    "шансон": "Концерт",
    "авторская песня": "Концерт",
    "хип-хоп": "Концерт",
    "фолк": "Концерт",
    "этно": "Концерт",
    "эстрада": "Концерт",

    "спектакли": "Театр",
    "драматический": "Театр",
    "мюзиклы": "Театр",
    "комедия": "Театр",

    "выставка": "Выставка",

    "экскурсии": "Экскурсия",

    "детям": "Для детей",
    "детский": "Для детей",
    "интерактивная": "Для детей",

    "мастер-классы": "Мастер-класс",

    "наука": "Наука",

    "шоу": "Другое",
    "стендап": "Другое",
    "юмор": "Другое",
    "литература": "Другое",
    "неизвестно": "Другое"
}

def normalize_category(raw_categories: str) -> str:
    """Приводит категории к единому формату согласно фильтрам"""
    categories = raw_categories.lower().split(", ")  # Разбиваем строку
    normalized = set()

    for category in categories:
        category = category.strip()
        if category in CATEGORY_MAPPING:
            normalized.add(CATEGORY_MAPPING[category])
        else:
            normalized.add("Другое")  # Если не найдено в списке, отправляем в "Другое"

    return ", ".join(sorted(normalized))  # Объединяем обратно

from datetime import datetime, date
import re

def clean_date(date_text):
    """Приводит дату к формату date (YYYY-MM-DD)"""

    # Словарь для преобразования месяцев
    months_dict = {
        'янв': '01', 'фев': '02', 'мар': '03', 'апр': '04',
        'мая': '05', 'июн': '06', 'июл': '07', 'авг': '08',
        'сен': '09', 'окт': '10', 'ноя': '11', 'дек': '12'
    }

    # Убираем неразрывные пробелы и пробелы по краям
    date_text = date_text.strip().replace("\xa0", " ")

    # Поиск формата "12 мая" или "17 апр"
    match = re.search(r"(\d{1,2})\s(\w+)", date_text)
    if match:
        day = match.group(1)  # Число
        month = match.group(2)  # Название месяца

        # Проверяем, есть ли месяц в словаре
        if month in months_dict:
            month_number = months_dict[month]

            # Получаем текущий год
            current_year = datetime.now().year

            # Проверяем, не прошла ли дата в этом году
            event_date = date(current_year, int(month_number), int(day))
            today = date.today()

            # Если дата уже прошла в этом году, используем следующий год
            if event_date < today:
                event_date = date(current_year + 1, int(month_number), int(day))

            return event_date  # Возвращаем объект типа date

    return None  # Если дата не распознана, возвращаем None



# Маппинг русских месяцев в числовой формат
MONTHS = {
    "января": "01", "февраля": "02", "марта": "03", "апреля": "04",
    "мая": "05", "июня": "06", "июля": "07", "августа": "08",
    "сентября": "09", "октября": "10", "ноября": "11", "декабря": "12"
}


def find_nearest_date(date_str: str) -> date | None:
    """ Преобразует строку с датой в формат `date`, выбирая ближайшую из списка """

    # Удаляем время (например, "в 19:00")
    date_str = re.sub(r"\s+в\s+\d{1,2}:\d{2}", "", date_str)

    # Убираем "и" и разделяем числа (например, "12, 19 и 26 марта" → ["12", "19", "26"])
    date_str = date_str.replace(" и ", ", ")

    # Разбиваем строку на части
    parts = date_str.split()
    if len(parts) < 2:
        return None  # Если формат неверный

    *days, month = parts  # Последнее слово — это месяц, остальные элементы — числа

    if month not in MONTHS:
        return None  # Если месяц не найден в словаре

    current_date = date.today()
    current_year = current_date.year
    current_month = current_date.month
    month_num = int(MONTHS[month])

    # Определяем год (если месяц уже прошел в этом году, берем следующий год)
    year = current_year if month_num >= current_month else current_year + 1

    # Ищем ближайшую подходящую дату
    valid_dates = []
    for day in days:
        try:
            event_date = date(year, month_num, int(day))
            if event_date >= current_date:
                valid_dates.append(event_date)
        except ValueError:
            continue

    if not valid_dates:
        return None  # Если нет будущих дат, возвращаем None

    return min(valid_dates)  # Возвращаем ближайшую дату в формате date


def log_memory_usage():
    mem = psutil.virtual_memory()
    logger.info(f"📊 Память перед запуском Chrome: {mem.available / (1024 * 1024)} MB свободно")