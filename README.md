# Telegram Profile Manager Bot

Бот для автоматического управления профилем Telegram, позволяющий создавать и переключаться между различными наборами имени и статуса.

## Установка

1. Установите Python 3.8 или выше
2. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Настройка

1. Получите `API_ID` и `API_HASH` на сайте https://my.telegram.org
2. Создайте нового бота через @BotFather и получите `BOT_TOKEN`
3. Узнайте свой Telegram ID через @userinfobot
4. Создайте файл `.env` со следующими данными:
```
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
OWNER_ID=your_telegram_id
```

## Запуск

### Windows
Запустите `start_bot.bat`

### Linux/Mac
```bash
python telegram_profile_bot.py
```

## Использование

1. Начните чат с ботом командой `/start`
2. Используйте команду `/add_profile` для добавления нового профиля
3. Используйте команду `/profiles` для просмотра доступных профилей
4. Нажмите на название профиля для его активации

## Установка как службы Windows

1. Запустите `install_service.bat` от имени администратора
2. Служба будет установлена и запущена автоматически
3. Для удаления службы используйте `uninstall_service.bat` 