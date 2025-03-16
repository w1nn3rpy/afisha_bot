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

# === Запрашиваем переменные ===
read -p "Введите POSTGRES_USER: " POSTGRES_USER
read -s -p "Введите POSTGRES_PASSWORD: " POSTGRES_PASSWORD
echo
read -p "Введите POSTGRES_DB: " POSTGRES_DB

# === Установка зависимостей ===
check_install "make" "make"
check_install "docker" "docker.io"
check_install "docker-compose" "docker-compose"

# === Обновляем docker-compose.yml с введёнными переменными ===
echo "🔹 Обновляем docker-compose.yml..."

sed -i "s/POSTGRES_USER: .*/POSTGRES_USER: ${POSTGRES_USER}/" docker-compose.yml
sed -i "s/POSTGRES_PASSWORD: .*/POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}/" docker-compose.yml
sed -i "s/POSTGRES_DB: .*/POSTGRES_DB: ${POSTGRES_DB}/" docker-compose.yml

# === Запуск контейнеров ===
echo "🔹 Запускаем docker-compose..."
docker-compose up -d

# === Добавляем новый адрес для подключения к БД в .env ===
sed -i "s|DATABASE_URL=.*|DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}|" .env

# === Запуск Dockerfile ===
echo "🔹 Собираем и запускаем Docker-контейнер..."
make build
make run
echo "✅ Установка завершена!"