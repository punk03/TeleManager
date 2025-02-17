@echo off
chcp 65001 > nul
setlocal

:: Проверка на права администратора
NET SESSION >nul 2>&1
if %errorLevel% neq 0 (
    echo Требуются права администратора!
    echo Пожалуйста, запустите скрипт от имени администратора.
    pause
    exit /b 1
)

echo Установка необходимых зависимостей...
pip install -r requirements.txt
if errorlevel 1 (
    echo Ошибка при установке зависимостей!
    pause
    exit /b 1
)

echo.
echo Установка службы...
python install_service.py
if errorlevel 1 (
    echo Ошибка при установке службы!
    pause
    exit /b 1
)

echo.
echo Готово! Служба установлена.
pause 