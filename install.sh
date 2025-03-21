#!/bin/bash

set -e  # Остановить выполнение при ошибке

# === Функция для проверки установленного пакета ===
check_install() {
    if ! command -v "$1" &> /dev/null; then
        echo "🔹 Устанавливаем $1..."
        sudo apt update
        sudo apt install -y "$2"
    else
        echo "✅ $1 уже установлен."
    fi
}

# === Установка зависимостей ===
check_install "make" "make"
check_install "docker" "docker.io"

# === Запрос на запуск БД ===
read -p "Хотите запустить PostgreSQL? [Y/n]: " RUN_DB
RUN_DB=${RUN_DB:-Y}  # Если ввод пустой, то по умолчанию Y

if [[ "$RUN_DB" =~ ^[Yy]$ ]]; then
    # === Запрашиваем переменные PostgreSQL ===
    read -p "Введите POSTGRES_USER (рекомендуется 'postgres'): " POSTGRES_USER
    read -s -p "Введите POSTGRES_PASSWORD: " POSTGRES_PASSWORD
    echo
    read -p "Введите POSTGRES_DB (рекомендуется 'afisha_db'): " POSTGRES_DB

    # === Обновляем docker-compose.yml и .env с введёнными переменными ===
    echo "🔹 Обновляем docker-compose.yml..."

    sed -i "s/POSTGRES_USER: .*/POSTGRES_USER: ${POSTGRES_USER}/" docker-compose.yml
    sed -i "s/POSTGRES_PASSWORD: .*/POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}/" docker-compose.yml
    sed -i "s/POSTGRES_DB: .*/POSTGRES_DB: ${POSTGRES_DB}/" docker-compose.yml
    sed -i "s|DATABASE_URL=.*|DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}|" .env

    # === Запуск контейнеров PostgreSQL ===
    echo "🔹 Запускаем docker-compose..."
    docker-compose up -d
else
    echo "⏩ Пропускаем запуск БД."
fi

# === Запрос на запуск бота ===
read -p "Хотите запустить бота? [Y/n]: " RUN_BOT
RUN_BOT=${RUN_BOT:-Y}

if [[ "$RUN_BOT" =~ ^[Yy]$ ]]; then
    # === Запрашиваем токен бота ===
    read -p "Введите токен бота Telegram: " BOT_TOKEN

    # === Добавляем новый токен в .env ===
    sed -i "s/BOT_TOKEN: .*/BOT_TOKEN: ${BOT_TOKEN}/" .env

    # === Запуск Docker-контейнера бота ===
    echo "🔹 Собираем и запускаем Docker-контейнер..."
    make build
    make run
else
    echo "⏩ Пропускаем запуск бота."
fi

echo "✅ Установка завершена!"
