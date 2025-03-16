FROM python:3.10-slim

WORKDIR /usr/src/app

RUN apt-get update && \
    apt-get install -y xvfb && \
    apt-get install -y google-chrome-stable=133.0.6943.126 && \
    apt-get clean && rm -rf /var/lib/apt/lists/* \

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3.10", "main.py"]

LABEL authors="w1nn3rpy"
