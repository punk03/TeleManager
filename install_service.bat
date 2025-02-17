@echo off
echo Установка виртуального окружения...
python -m venv venv
call venv\Scripts\activate.bat

echo Установка зависимостей...
pip install -r requirements.txt

echo Установка службы...
python windows_service.py install

echo Запуск службы...
python windows_service.py start

echo Готово! Служба установлена и запущена.
pause 