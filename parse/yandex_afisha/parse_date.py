import datetime
import re
import locale

# Попытка установить русскую локаль
try:
    locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")
except locale.Error:
    print("⚠️ Локаль 'ru_RU.UTF-8' не поддерживается, используем системную локаль.")

# Преобразование месяцев из родительного падежа в именительный
MONTHS = {
    "января": "январь", "февраля": "февраль", "марта": "март", "апреля": "апрель",
    "мая": "май", "июня": "июнь", "июля": "июль", "августа": "август",
    "сентября": "сентябрь", "октября": "октябрь", "ноября": "ноябрь", "декабря": "декабрь"
}

def parse_event_date(date_str: str) -> datetime.date:
    """
    Преобразует строку с датой в объект datetime.date.
    Берёт **последний день** из диапазонов или **последний месяц** в случае периода.

    Поддерживает:
    - "10 апреля, 19:00" → 10 апреля
    - "сегодня 18 марта, 19:00" → 18 марта
    - "пт 21 марта, 19:00" → 21 марта
    - "20 и 27 марта" → 27 марта
    - "март — декабрь" → 1 декабря
    - Проверяет год: если месяц прошёл, устанавливает следующий год
    """

    today = datetime.date.today()
    current_year = today.year

    # 1️⃣ **Обрабатываем "сегодня" и "завтра"**
    if "сегодня" in date_str:
        return today

    if "завтра" in date_str:
        return today + datetime.timedelta(days=1)

    # 2️⃣ **Удаляем день недели ("пт", "сб", и т. д.)** перед разбором даты
    date_str = re.sub(r"^\w{2,3} ", "", date_str)

    # 3️⃣ **Поиск даты "10 апреля, 19:00"**
    match = re.search(r"(\d{1,2}) (\w+)", date_str)
    if match:
        day, month = match.groups()
        month = MONTHS.get(month, month)  # Приводим месяц к именительному падежу
        try:
            month_number = datetime.datetime.strptime(month, "%B").month
            event_year = current_year if month_number >= today.month else current_year + 1
            return datetime.date(event_year, month_number, int(day))
        except ValueError as e:
            print(f"⚠️ Ошибка парсинга даты [{date_str}]: {e}")

    # 4️⃣ **Обрабатываем диапазон месяцев ("март — декабрь")**
    match = re.search(r"(\w+) — (\w+)", date_str)
    if match:
        _, last_month = match.groups()
        last_month = MONTHS.get(last_month, last_month)
        try:
            month_number = datetime.datetime.strptime(last_month, "%B").month
            event_year = current_year if month_number >= today.month else current_year + 1
            return datetime.date(event_year, month_number, 1)  # Берём 1-е число последнего месяца
        except ValueError as e:
            print(f"⚠️ Ошибка парсинга даты [{date_str}]: {e}")

    # 5️⃣ **Обрабатываем диапазон дней ("20 и 27 марта")**
    match = re.search(r"(\d{1,2}) и (\d{1,2}) (\w+)", date_str)
    if match:
        _, last_day, month = match.groups()
        month = MONTHS.get(month, month)
        try:
            month_number = datetime.datetime.strptime(month, "%B").month
            event_year = current_year if month_number >= today.month else current_year + 1
            return datetime.date(event_year, month_number, int(last_day))
        except ValueError as e:
            print(f"⚠️ Ошибка парсинга даты [{date_str}]: {e}")

    # Если ничего не получилось разобрать, выбрасываем ошибку
    raise ValueError(f"Не удалось распарсить дату: {date_str}")
