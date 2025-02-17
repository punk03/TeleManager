@echo off
chcp 65001 > nul
setlocal

echo Установка необходимых зависимостей...
pip install -r requirements.txt
if errorlevel 1 (
    echo Ошибка при установке зависимостей!
    pause
    exit /b 1
)

echo.
echo Запуск бота в трее...
start /min pythonw tray_bot.py

echo Бот запущен и работает в фоновом режиме.
echo Иконка бота находится в системном трее.
timeout /t 5 