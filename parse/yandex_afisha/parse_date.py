import datetime
import re
import locale
import calendar

# Устанавливаем русскую локаль для работы с названиями месяцев
try:
    locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")
except locale.Error:
    pass  # В случае ошибки продолжаем без локали

def parse_event_date(date_str: str) -> datetime.date:
    """
    Преобразует строку с датой в объект datetime.date.

    Поддерживает:
    - "сб 22 марта, 18:00" → 22 марта
    - "сегодня 18 марта, 19:00" → 18 марта
    - "4 мая, 19:00" → 4 мая
    - "20 и 27 марта" → 27 марта
    - "март — декабрь" → 31 декабря (последний день месяца)
    - "апрель" → 30 апреля (последний день месяца)
    """

    today = datetime.date.today()

    # Если в строке есть "сегодня", заменяем на текущую дату
    if "сегодня" in date_str:
        match = re.search(r"(\d{1,2}) (\w+)", date_str)
        if match:
            day, month = match.groups()
            month_number = datetime.datetime.strptime(month, "%B").month
            return datetime.date(today.year, month_number, int(day))
        return today

    # Если в строке есть "завтра", берём следующий день
    if "завтра" in date_str:
        return today + datetime.timedelta(days=1)

    # Поиск формата "22 марта, 18:00"
    match = re.search(r"(\d{1,2}) (\w+)", date_str)
    if match:
        day, month = match.groups()
        try:
            month_number = datetime.datetime.strptime(month, "%B").month
            return datetime.date(today.year, month_number, int(day))
        except ValueError:
            pass

    # Если указан диапазон месяцев ("март — декабрь"), берём последний день последнего месяца
    match = re.search(r"(\w+) — (\w+)", date_str)
    if match:
        _, last_month = match.groups()
        try:
            month_number = datetime.datetime.strptime(last_month, "%B").month
            last_day = calendar.monthrange(today.year, month_number)[1]  # Последний день месяца
            return datetime.date(today.year, month_number, last_day)
        except ValueError:
            pass

    # Если есть диапазон дат ("20 и 27 марта"), берём **последний день**
    match = re.search(r"(\d{1,2}) и (\d{1,2}) (\w+)", date_str)
    if match:
        _, last_day, month = match.groups()
        try:
            month_number = datetime.datetime.strptime(month, "%B").month
            return datetime.date(today.year, month_number, int(last_day))
        except ValueError:
            pass

    # Если указано только название месяца, выбираем последний день этого месяца
    match = re.search(r"^(\w+)$", date_str.strip())
    if match:
        month = match.group(1)
        try:
            month_number = datetime.datetime.strptime(month, "%B").month
            last_day = calendar.monthrange(today.year, month_number)[1]
            return datetime.date(today.year, month_number, last_day)
        except ValueError:
            pass

    raise ValueError(f"❌ Не удалось распарсить дату: {date_str}")