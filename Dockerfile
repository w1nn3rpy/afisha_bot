FROM python:3.10-slim

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y wget unzip xvfb && \
    CHROME_VERSION="133.0.6943.126" && \
    wget -O /tmp/chrome-linux64.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chrome-linux64.zip" && \
    unzip /tmp/chrome-linux64.zip -d /opt/ && \
    mv /opt/chrome-linux64 /opt/google-chrome && \
    ln -s /opt/google-chrome/chrome /usr/bin/google-chrome && \
    rm -rf /tmp/chrome-linux64.zip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3.10", "main.py"]

LABEL authors="w1nn3rpy"
