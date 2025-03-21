FROM python:3.10-slim

WORKDIR /usr/src/app

COPY requirements.txt ./

# Установка необходимых пакетов + локаль ru_RU.UTF-8
RUN apt-get update && apt-get install -y \
    wget unzip xvfb locales \
    libglib2.0-0 libnss3 libgconf-2-4 libfontconfig1 \
    libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 \
    libxi6 libxrandr2 libgbm1 libasound2 libatk1.0-0 libpangocairo-1.0-0 \
    libatk-bridge2.0-0 libgtk-3-0 && \
    # Установка русской локали
    locale-gen ru_RU.UTF-8 && \
    update-locale LANG=ru_RU.UTF-8 && \
    export LANG=ru_RU.UTF-8 && \
    export LC_ALL=ru_RU.UTF-8 && \
    # Установка Chrome и ChromeDriver
    CHROME_VERSION="134.0.6998.88" && \
    wget -O /tmp/chrome-linux64.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chrome-linux64.zip" && \
    unzip /tmp/chrome-linux64.zip -d /opt/ && \
    mv /opt/chrome-linux64 /opt/google-chrome && \
    ln -s /opt/google-chrome/chrome /usr/bin/google-chrome && \
    rm -rf /tmp/chrome-linux64.zip && \
    wget -O /tmp/chromedriver-linux64.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" && \
    unzip /tmp/chromedriver-linux64.zip -d /opt/ && \
    mv /opt/chromedriver-linux64/chromedriver /opt/chromedriver && \
    ln -s /opt/chromedriver /usr/bin/chromedriver && \
    rm -rf /tmp/chromedriver-linux64.zip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Установка зависимостей Python
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Добавляем ENV для локали, чтобы Python подхватывал ru_RU.UTF-8
ENV LANG=ru_RU.UTF-8 \
    LC_ALL=ru_RU.UTF-8

CMD ["python3.10", "main.py"]

LABEL authors="w1nn3rpy"
