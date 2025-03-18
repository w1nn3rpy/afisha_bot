import datetime
import re
import locale

# Устанавливаем русскую локаль для работы с названиями месяцев
locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")


def parse_event_date(date_str: str) -> datetime.date:
    """
    Преобразует строку с датой в объект datetime.date.
    Теперь берётся **последний день** из диапазонов или **последний месяц** в случае периода.

    Поддерживает:
    - "сб 22 марта, 18:00" → 22 марта
    - "сегодня 18 марта, 19:00" → 18 марта
    - "4 мая, 19:00" → 4 мая
    - "20 и 27 марта" → 27 марта
    - "март — декабрь" → 1 декабря
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

    # Если указан диапазон месяцев ("март — декабрь"), берём последний месяц
    match = re.search(r"(\w+) — (\w+)", date_str)
    if match:
        _, last_month = match.groups()
        try:
            month_number = datetime.datetime.strptime(last_month, "%B").month
            return datetime.date(today.year, month_number, 1)  # Берём 1-е число последнего месяца
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

    raise ValueError(f"Не удалось распарсить дату: {date_str}")

