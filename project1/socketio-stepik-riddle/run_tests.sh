#!/bin/bash

echo "Запуск приложения..."
python3 main.py &
APP_PID=$!

sleep 2

echo "Запуск тестов..."
pytest -q --disable-warnings tests/

echo "Остановка приложения..."
kill $APP_PID

echo "Скрипт завершён."
