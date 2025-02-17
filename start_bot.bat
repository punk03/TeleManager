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
echo Telegram Profile Bot
echo -------------------
echo 1. Запустить в обычном режиме
echo 2. Запустить в режиме отладки
echo -------------------
set /p choice="Выберите режим запуска (1/2): "

if "%choice%"=="1" (
    python telegram_profile_bot.py
) else if "%choice%"=="2" (
    python telegram_profile_bot.py --debug
) else (
    echo Неверный выбор. Запускаю в обычном режиме...
    python telegram_profile_bot.py
)

pause 