@echo off
echo Остановка службы...
python windows_service.py stop

echo Удаление службы...
python windows_service.py remove

echo Готово! Служба удалена.
pause 