# Telegram Profile Manager Bot

Бот для автоматического управления профилем Telegram, позволяющий создавать и переключаться между различными наборами имени, фамилии, статуса и эмодзи-статуса.

> 📚 [Подробное руководство по использованию бота](GUIDE.md)

## Возможности

- 👤 Управление несколькими профилями (имя, фамилия)
- 💭 Установка статуса для каждого профиля
- 🎭 Поддержка эмодзи-статусов Telegram Premium
- ⏱ Временное включение профиля
- 📅 Расписание автоматической смены профилей
- 🔄 Мгновенное переключение между профилями

## Установка

### Способ 1: Обычная установка

1. Установите Python 3.8 или выше
2. Клонируйте репозиторий:
```bash
git clone https://github.com/punk03/TeleManager.git
cd TeleManager
```
3. Установите зависимости:
```bash
pip install -r requirements.txt
```

### Способ 2: Установка через Docker

1. Установите [Docker](https://docs.docker.com/get-docker/) и [Docker Compose](https://docs.docker.com/compose/install/)
2. Клонируйте репозиторий:
```bash
git clone https://github.com/punk03/TeleManager.git
cd TeleManager
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

### Способ 1: Обычный запуск

#### Windows
Запустите `start_bot.bat`

#### Linux/Mac
```bash
python telegram_profile_bot.py
```

### Способ 2: Запуск через Docker

1. Соберите и запустите контейнер:
```bash
docker-compose up -d --build
```

2. Просмотр логов:
```bash
docker-compose logs -f
```

3. Остановка бота:
```bash
docker-compose down
```

### Управление данными в Docker

- Все сессии сохраняются в директории `sessions/`
- Профили хранятся в файле `profiles.json`
- Конфигурация в директории `config/`
- Все данные сохраняются между перезапусками контейнера

## Использование

1. Начните чат с ботом командой `/start`
2. Используйте кнопку "➕ Добавить профиль" для создания нового профиля:
   - Введите название профиля
   - Введите имя
   - Введите фамилию (или отправьте '-' чтобы пропустить)
   - Введите статус с эмодзи
   - Для Premium пользователей: перешлите боту любое сообщение для получения ID текущего эмодзи-статуса
3. Используйте "📋 Список профилей" для управления профилями:
   - 🔄 Включить постоянно
   - ⏱ Включить на время (30 минут - 5 часов)
   - 📅 Включить до следующего расписания
   - ✏️ Редактировать
   - ❌ Удалить
4. Используйте "📅 Расписание" для настройки автоматической смены профилей

## Установка как службы Windows

> ⚠️ Этот метод доступен только при обычной установке (не Docker)

1. Запустите `install_service.bat` от имени администратора
2. Служба будет установлена и запущена автоматически
3. Для удаления службы используйте `uninstall_service.bat`

## Безопасность

- Бот работает только с одним владельцем (указанным в OWNER_ID)
- Все конфиденциальные данные хранятся в файле .env
- Сессии Telegram хранятся локально
- При использовании Docker все данные изолированы в контейнере

## Примечания

- Для использования эмодзи-статусов требуется Telegram Premium
- При первом запуске потребуется авторизация в вашем аккаунте Telegram
- В Docker-версии все данные сохраняются в volumes и доступны между перезапусками
- Часовой пояс в Docker-контейнере установлен на Europe/Moscow (можно изменить в docker-compose.yml) 