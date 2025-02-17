from telethon import TelegramClient, events, Button
from telethon.tl.functions.account import UpdateProfileRequest, UpdateEmojiStatusRequest
from telethon.tl.types import EmojiStatus
import asyncio
from datetime import datetime, timedelta
import json
import logging
import sys
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config.config import API_ID, API_HASH, BOT_TOKEN, PROFILES_FILE, SESSION_NAME, OWNER_ID

def setup_logging(debug_mode):
    """Настройка логирования"""
    if debug_mode:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            stream=sys.stdout
        )
        # Включаем логирование Telethon
        client_logger = logging.getLogger('telethon')
        client_logger.setLevel(logging.DEBUG)
        # Включаем логирование APScheduler
        scheduler_logger = logging.getLogger('apscheduler')
        scheduler_logger.setLevel(logging.DEBUG)
    else:
        logging.basicConfig(
            level=logging.WARNING,
            format='%(asctime)s - %(levelname)s - %(message)s',
            stream=sys.stdout
        )

# Состояния для FSM
STATES = {}
# Загрузка предустановленных профилей
def load_profiles():
    try:
        with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:  # Если файл пустой
                return {}
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError):
        # Создаем новый файл с пустым словарем
        with open(PROFILES_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4, ensure_ascii=False)
        return {}

def save_profiles(profiles):
    with open(PROFILES_FILE, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, indent=4, ensure_ascii=False)

PRESET_PROFILES = load_profiles()

# Создаем два клиента - один для бота, другой для изменения профиля
bot_client = TelegramClient(SESSION_NAME + "_bot", API_ID, API_HASH)
user_client = TelegramClient(SESSION_NAME + "_user", API_ID, API_HASH)
scheduler = AsyncIOScheduler()

# Глобальная переменная для хранения ID последнего сообщения с уведомлением
LAST_NOTIFICATION = None

async def send_notification(message):
    """Отправка уведомления в чат с ботом"""
    global LAST_NOTIFICATION
    try:
        if LAST_NOTIFICATION:
            try:
                await LAST_NOTIFICATION.delete()
            except:
                pass
        LAST_NOTIFICATION = await bot_client.send_message(OWNER_ID, message)
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления: {e}")

def is_owner(event):
    """Проверка, является ли отправитель владельцем бота"""
    return event.sender_id == OWNER_ID

async def change_profile(profile_name, notify=True):
    """Изменение профиля с опциональным уведомлением"""
    if profile_name in PRESET_PROFILES:
        profile = PRESET_PROFILES[profile_name]
        await user_client(UpdateProfileRequest(
            first_name=profile['first_name'],
            last_name=profile.get('last_name', '')
        ))
        if 'emoji_status' in profile and profile['emoji_status']:
            try:
                await user_client(UpdateEmojiStatusRequest(
                    emoji_status=EmojiStatus(document_id=int(profile['emoji_status']))
                ))
            except Exception as e:
                logging.error(f"Ошибка при установке эмодзи-статуса: {e}")
        
        if notify:
            current_time = datetime.now().strftime("%H:%M")
            notification = f"🔄 Профиль изменен на «{profile_name}» в {current_time}\n"
            notification += f"👤 Имя: {profile['first_name']}\n"
            if profile.get('last_name'):
                notification += f"👥 Фамилия: {profile['last_name']}\n"
            if profile.get('status'):
                notification += f"💭 Статус: {profile['status']}\n"
            await send_notification(notification)
        
        return f"Профиль изменен на {profile_name}"
    return "Профиль не найден"

async def get_main_keyboard():
    """Создание основной клавиатуры"""
    return [
        [Button.text("📋 Список профилей"), Button.text("➕ Добавить профиль")],
        [Button.text("📅 Расписание"), Button.text("ℹ️ Помощь")]
    ]

async def get_profiles_keyboard():
    """Создание клавиатуры с профилями"""
    keyboard = []
    for profile_name in PRESET_PROFILES.keys():
        keyboard.append([Button.text(f"👤 {profile_name}")])
    keyboard.append([Button.text("◀️ Назад")])
    return keyboard

async def get_profile_actions_keyboard(profile_name):
    """Создание клавиатуры действий для конкретного профиля"""
    return [
        [Button.text("🔄 Включить постоянно")],
        [Button.text("⏱ Включить на время")],
        [Button.text("📅 Включить до расписания")],
        [Button.text("✏️ Редактировать")],
        [Button.text("❌ Удалить")],
        [Button.text("◀️ К списку профилей")]
    ]

async def get_schedule_keyboard():
    """Создание клавиатуры для расписания"""
    keyboard = []
    for profile_name in PRESET_PROFILES.keys():
        keyboard.append([
            Button.text(f"⏰ {profile_name}")
        ])
    keyboard.append([Button.text("📋 Список расписаний")])
    keyboard.append([Button.text("🗑 Очистить расписание")])
    keyboard.append([Button.text("◀️ Назад")])
    return keyboard

async def get_duration_keyboard():
    """Создание клавиатуры для выбора длительности"""
    return [
        [Button.text("30 минут"), Button.text("1 час"), Button.text("2 часа")],
        [Button.text("3 часа"), Button.text("4 часа"), Button.text("5 часов")],
        [Button.text("До следующего расписания")],
        [Button.text("◀️ Отмена")]
    ]

@bot_client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if not is_owner(event):
        await event.reply("Извините, но этот бот доступен только для его владельца.")
        return

    await event.reply(
        "Привет! Я бот для управления профилем Telegram.",
        buttons=await get_main_keyboard()
    )

@bot_client.on(events.NewMessage(func=lambda e: e.text == "📋 Список профилей"))
async def profiles_handler(event):
    if not is_owner(event):
        return

    if not PRESET_PROFILES:
        await event.reply(
            "У вас пока нет сохраненных профилей. Добавьте новый профиль!",
            buttons=await get_main_keyboard()
        )
        return

    profiles_text = "Доступные профили:\n\n"
    for name, profile in PRESET_PROFILES.items():
        profiles_text += f"📌 {name}\n"
        profiles_text += f"👤 Имя: {profile['first_name']}\n"
        profiles_text += f"👥 Фамилия: {profile['last_name']}\n\n"

    await event.reply(
        profiles_text,
        buttons=await get_profiles_keyboard()
    )

@bot_client.on(events.NewMessage(func=lambda e: e.text == "➕ Добавить профиль"))
async def add_profile_start(event):
    if not is_owner(event):
        return

    STATES[event.sender_id] = {"state": "waiting_profile_name"}
    await event.reply(
        "Введите название нового профиля:",
        buttons=[[Button.text("◀️ Отмена")]]
    )

@bot_client.on(events.NewMessage(func=lambda e: e.text == "◀️ Отмена" or e.text == "◀️ Назад" or e.text == "◀️ К списку профилей"))
async def universal_back_handler(event):
    if not is_owner(event):
        return

    # Очищаем состояние, если оно есть
    if event.sender_id in STATES:
        del STATES[event.sender_id]
    
    # Определяем, куда возвращаться
    if event.text == "◀️ К списку профилей":
        # Возврат к списку профилей
        profiles_text = "Доступные профили:\n\n"
        for name, profile in PRESET_PROFILES.items():
            profiles_text += f"📌 {name}\n"
            profiles_text += f"👤 Имя: {profile['first_name']}\n"
            profiles_text += f"👥 Фамилия: {profile['last_name']}\n\n"

        await event.reply(
            profiles_text,
            buttons=await get_profiles_keyboard()
        )
    else:
        # Возврат в главное меню
        await event.reply(
            "Возвращаемся в главное меню",
            buttons=await get_main_keyboard()
        )

@bot_client.on(events.NewMessage(func=lambda e: e.sender_id in STATES))
async def profile_creation_handler(event):
    if not is_owner(event):
        return

    if event.text in ["◀️ Отмена", "◀️ Назад", "📋 Список профилей", "➕ Добавить профиль", "📅 Расписание", "ℹ️ Помощь"]:
        return

    state = STATES[event.sender_id]
    
    if state["state"] == "waiting_profile_name":
        if event.text in PRESET_PROFILES:
            await event.reply("Такой профиль уже существует. Выберите другое название:")
            return
        
        state["profile_name"] = event.text
        state["state"] = "waiting_first_name"
        await event.reply("Введите имя для профиля:")
    
    elif state["state"] == "waiting_first_name":
        state["first_name"] = event.text
        state["state"] = "waiting_last_name"
        await event.reply("Введите фамилию для профиля:")
    
    elif state["state"] == "waiting_last_name":
        state["last_name"] = event.text
        state["state"] = "waiting_emoji_status"
        await event.reply(
            "Введите ID эмодзи-статуса (или отправьте 0, чтобы пропустить):\n\n"
            "Чтобы получить ID статуса:\n"
            "1. Установите нужный статус через официальный клиент\n"
            "2. Перешлите любое сообщение боту\n"
            "3. Бот покажет ID вашего текущего статуса"
        )
    
    elif state["state"] == "waiting_emoji_status":
        emoji_status = "0"
        if event.text != "0":
            try:
                emoji_status = str(int(event.text))  # Проверяем, что введено число
            except ValueError:
                await event.reply("Пожалуйста, введите числовой ID статуса или 0, чтобы пропустить:")
                return

        PRESET_PROFILES[state["profile_name"]] = {
            "first_name": state["first_name"],
            "last_name": state["last_name"],
            "emoji_status": emoji_status if emoji_status != "0" else None
        }
        save_profiles(PRESET_PROFILES)
        del STATES[event.sender_id]
        
        await event.reply(
            f"Профиль {state['profile_name']} успешно создан!",
            buttons=await get_main_keyboard()
        )

@bot_client.on(events.NewMessage(func=lambda e: e.text.startswith("👤 ")))
async def profile_menu_handler(event):
    if not is_owner(event):
        return

    profile_name = event.text[2:].strip()
    if profile_name not in PRESET_PROFILES:
        await event.reply("Профиль не найден", buttons=await get_profiles_keyboard())
        return

    profile = PRESET_PROFILES[profile_name]
    profile_text = f"Профиль: {profile_name}\n"
    profile_text += f"👤 Имя: {profile['first_name']}\n"
    profile_text += f"👥 Фамилия: {profile['last_name']}\n"
    if profile.get('emoji_status'):
        profile_text += f"🎭 Эмодзи-статус: {profile['emoji_status']}\n"
    profile_text += "\nВыберите действие:"

    # Сохраняем текущий профиль в состоянии
    STATES[event.sender_id] = {"state": "profile_menu", "profile_name": profile_name}

    await event.reply(
        profile_text,
        buttons=await get_profile_actions_keyboard(profile_name)
    )
    raise events.StopPropagation()

@bot_client.on(events.NewMessage(pattern=r"^📅 Расписание$"))
async def schedule_handler(event):
    if not is_owner(event):
        return
    
    if not PRESET_PROFILES:
        await event.reply(
            "У вас пока нет сохраненных профилей. Добавьте новый профиль!",
            buttons=await get_main_keyboard()
        )
        return

    # Получаем список активных задач
    jobs = scheduler.get_jobs()
    schedule_text = "📅 Управление расписанием\n\n"
    
    if jobs:
        schedule_text += "Активные расписания:\n"
        for job in jobs:
            if not job.id.startswith('temp_'):  # Пропускаем временные задачи
                if job.args and len(job.args) > 0:
                    profile_name = job.args[0]
                    if profile_name in PRESET_PROFILES:  # Проверяем существование профиля
                        next_run = job.next_run_time.strftime("%H:%M")
                        schedule_text += f"⏰ {profile_name} - следующая смена в {next_run}\n"
    else:
        schedule_text += "Нет активных расписаний\n"
    
    schedule_text += "\nВыберите профиль для настройки расписания:"
    
    await event.reply(
        schedule_text,
        buttons=await get_schedule_keyboard()
    )
    raise events.StopPropagation()

@bot_client.on(events.NewMessage(func=lambda e: e.text == "📋 Список расписаний"))
async def list_schedules_handler(event):
    if not is_owner(event):
        return

    jobs = scheduler.get_jobs()
    schedule_text = "📅 Активные расписания:\n\n"
    
    if not jobs:
        schedule_text = "Нет активных расписаний"
    else:
        for job in jobs:
            if not job.id.startswith('temp_'):
                profile_name = job.args[0] if job.args else "неизвестный профиль"
                trigger = job.trigger
                
                if isinstance(trigger, CronTrigger):
                    schedule_text += f"⏰ {profile_name}:\n"
                    schedule_text += f"   🕒 Время: {trigger.fields[3]:02d}:{trigger.fields[4]:02d}\n"
                    
                    # Добавляем информацию о днях недели
                    days = trigger.fields[5]
                    if days == "*":
                        schedule_text += "   📆 Дни: Ежедневно\n"
                    else:
                        day_names = {
                            0: "Понедельник", 1: "Вторник", 2: "Среда",
                            3: "Четверг", 4: "Пятница", 5: "Суббота", 6: "Воскресенье"
                        }
                        schedule_text += "   📆 Дни: " + ", ".join([day_names[d] for d in days]) + "\n"
                    schedule_text += "\n"

    await event.reply(schedule_text, buttons=await get_schedule_keyboard())

@bot_client.on(events.NewMessage(pattern=r"^⏰ .*$"))
async def schedule_profile_start(event):
    if not is_owner(event):
        return

    profile_name = event.text[2:].strip()
    if profile_name not in PRESET_PROFILES:
        await event.reply(
            "Ошибка: профиль не найден в списке профилей.",
            buttons=await get_schedule_keyboard()
        )
        return

    STATES[event.sender_id] = {
        "state": "waiting_schedule_days",
        "profile_name": profile_name
    }
    
    # Клавиатура для выбора дней недели
    days_keyboard = [
        [Button.text("Пн"), Button.text("Вт"), Button.text("Ср")],
        [Button.text("Чт"), Button.text("Пт"), Button.text("Сб")],
        [Button.text("Вс"), Button.text("Ежедневно")],
        [Button.text("◀️ Отмена")]
    ]
    
    await event.reply(
        f"Настройка расписания для профиля {profile_name}\n"
        "Выберите дни недели (можно выбрать несколько):",
        buttons=days_keyboard
    )
    raise events.StopPropagation()

@bot_client.on(events.NewMessage(func=lambda e: e.sender_id in STATES and STATES[e.sender_id]["state"] == "waiting_schedule_days"))
async def schedule_days_handler(event):
    if not is_owner(event):
        return

    state = STATES[event.sender_id]
    
    if event.text == "◀️ Отмена":
        del STATES[event.sender_id]
        await event.reply("Настройка расписания отменена.", buttons=await get_schedule_keyboard())
        return
    
    if event.text == "Ежедневно":
        state["days"] = "*"
    else:
        day_map = {
            "Пн": 0, "Вт": 1, "Ср": 2, "Чт": 3,
            "Пт": 4, "Сб": 5, "Вс": 6
        }
        if event.text not in day_map:
            await event.reply("Пожалуйста, выберите день из предложенных вариантов.")
            return
            
        if "days" not in state:
            state["days"] = set()
        state["days"].add(day_map[event.text])
    
    if isinstance(state["days"], set):
        days_text = ", ".join(k for k, v in day_map.items() if v in state["days"])
    else:
        days_text = "Ежедневно"
    
    state["state"] = "waiting_schedule_hour"
    await event.reply(
        f"Выбранные дни: {days_text}\n"
        "Теперь введите час (0-23):",
        buttons=[[Button.text("◀️ Отмена")]]
    )

@bot_client.on(events.NewMessage(func=lambda e: e.sender_id in STATES and STATES[e.sender_id]["state"] in ["waiting_schedule_hour", "waiting_schedule_minute"]))
async def schedule_time_handler(event):
    if not is_owner(event):
        return

    if event.text == "◀️ Отмена":
        del STATES[event.sender_id]
        await event.reply("Настройка расписания отменена.", buttons=await get_schedule_keyboard())
        return

    state = STATES[event.sender_id]
    
    try:
        if state["state"] == "waiting_schedule_hour":
            hour = int(event.text)
            if 0 <= hour <= 23:
                state["hour"] = hour
                state["state"] = "waiting_schedule_minute"
                await event.reply("Введите минуты (0-59):")
            else:
                await event.reply("Пожалуйста, введите число от 0 до 23:")
        
        elif state["state"] == "waiting_schedule_minute":
            minute = int(event.text)
            if 0 <= minute <= 59:
                # Удаляем существующие задачи для этого профиля
                for job in scheduler.get_jobs():
                    if job.args and job.args[0] == state["profile_name"]:
                        job.remove()
                
                # Добавляем новую задачу с учетом выбранных дней
                if state["days"] == "*":
                    scheduler.add_job(
                        change_profile,
                        'cron',
                        hour=state["hour"],
                        minute=minute,
                        args=[state["profile_name"]],
                        id=f'schedule_{state["profile_name"]}'
                    )
                else:
                    scheduler.add_job(
                        change_profile,
                        'cron',
                        day_of_week=",".join(str(d) for d in state["days"]),
                        hour=state["hour"],
                        minute=minute,
                        args=[state["profile_name"]],
                        id=f'schedule_{state["profile_name"]}'
                    )
                
                # Формируем сообщение о расписании
                if state["days"] == "*":
                    days_text = "ежедневно"
                else:
                    day_names = {
                        0: "понедельник", 1: "вторник", 2: "среда",
                        3: "четверг", 4: "пятница", 5: "суббота", 6: "воскресенье"
                    }
                    days_text = ", ".join(day_names[d] for d in state["days"])
                
                await event.reply(
                    f"Расписание установлено! Профиль {state['profile_name']} будет "
                    f"активироваться в {state['hour']:02d}:{minute:02d} "
                    f"по следующим дням: {days_text}",
                    buttons=await get_schedule_keyboard()
                )
                del STATES[event.sender_id]
            else:
                await event.reply("Пожалуйста, введите число от 0 до 59:")
    except ValueError:
        await event.reply("Пожалуйста, введите корректное число:")

@bot_client.on(events.NewMessage(func=lambda e: e.text == "🗑 Очистить расписание"))
async def clear_schedule_handler(event):
    if not is_owner(event):
        return

    scheduler.remove_all_jobs()
    await event.reply(
        "Все расписания очищены!",
        buttons=await get_schedule_keyboard()
    )

@bot_client.on(events.NewMessage(func=lambda e: e.text == "ℹ️ Помощь"))
async def help_handler(event):
    if not is_owner(event):
        return

    help_text = """
📱 Доступные команды:

📋 Список профилей - просмотр и управление профилями
➕ Добавить профиль - создание нового профиля
📅 Расписание - управление автоматической сменой профилей
ℹ️ Помощь - это сообщение

В списке профилей:
🔄 - применить профиль
✏️ - редактировать профиль
❌ - удалить профиль
    """
    await event.reply(help_text, buttons=await get_main_keyboard())

@bot_client.on(events.NewMessage(func=lambda e: e.sender_id in STATES and STATES[e.sender_id]["state"] == "waiting_duration"))
async def duration_handler(event):
    if not is_owner(event):
        return

    if event.text == "◀️ Отмена":
        del STATES[event.sender_id]
        await event.reply("Действие отменено.", buttons=await get_profiles_keyboard())
        return

    state = STATES[event.sender_id]
    profile_name = state["profile_name"]
    duration_map = {
        "30 минут": 30,
        "1 час": 60,
        "2 часа": 120,
        "3 часа": 180,
        "4 часа": 240,
        "5 часов": 300
    }

    if event.text == "До следующего расписания":
        # Находим следующую запланированную смену профиля
        next_job = None
        next_run_time = None
        for job in scheduler.get_jobs():
            if not job.id.startswith('temp_'):  # Пропускаем временные задачи
                if next_run_time is None or job.next_run_time < next_run_time:
                    next_job = job
                    next_run_time = job.next_run_time

        if next_run_time is None:
            await event.reply(
                "Нет активных расписаний. Профиль будет активен постоянно.",
                buttons=await get_profiles_keyboard()
            )
            await change_profile(profile_name)
        else:
            # Активируем профиль
            await change_profile(profile_name)
            
            # Форматируем время следующей смены
            next_change = next_run_time.strftime("%H:%M")
            next_profile = next_job.args[0] if next_job.args else "неизвестный профиль"
            
            await event.reply(
                f"Профиль {profile_name} активирован до {next_change} "
                f"(следующая автоматическая смена на {next_profile})",
                buttons=await get_profiles_keyboard()
            )
        
        del STATES[event.sender_id]
        return

    if event.text not in duration_map:
        await event.reply(
            "Пожалуйста, выберите длительность из предложенных вариантов:",
            buttons=await get_duration_keyboard()
        )
        return

    # Активируем профиль
    await change_profile(profile_name)
    
    # Получаем длительность в минутах
    duration = duration_map[event.text]
    
    # Удаляем существующие временные задачи для этого профиля
    for job in scheduler.get_jobs():
        if job.args and job.args[0] == profile_name and job.id.startswith('temp_'):
            job.remove()

    # Находим следующий профиль по расписанию
    next_scheduled_job = None
    for job in scheduler.get_jobs():
        if not job.id.startswith('temp_'):  # Пропускаем временные задачи
            if next_scheduled_job is None or job.next_run_time < next_scheduled_job.next_run_time:
                next_scheduled_job = job

    # Добавляем задачу на возврат к предыдущему профилю
    if next_scheduled_job and next_scheduled_job.next_run_time:
        temp_end_time = datetime.now() + timedelta(minutes=duration)
        
        if temp_end_time < next_scheduled_job.next_run_time:
            # Если временный профиль закончится раньше следующего по расписанию
            scheduler.add_job(
                change_profile,
                'date',
                run_date=temp_end_time,
                args=[next_scheduled_job.args[0]],
                id=f'temp_{profile_name}'
            )
            await event.reply(
                f"Профиль {profile_name} активирован на {event.text}.\n"
                f"В {temp_end_time.strftime('%H:%M')} будет возврат к профилю {next_scheduled_job.args[0]}",
                buttons=await get_profiles_keyboard()
            )
        else:
            # Если следующая смена по расписанию наступит раньше
            await event.reply(
                f"Профиль {profile_name} активирован до следующей смены по расписанию "
                f"в {next_scheduled_job.next_run_time.strftime('%H:%M')}",
                buttons=await get_profiles_keyboard()
            )
    else:
        # Если нет расписания, просто ставим таймер
        scheduler.add_job(
            change_profile,
            'date',
            run_date=datetime.now() + timedelta(minutes=duration),
            args=[profile_name],  # Возвращаемся к текущему профилю
            id=f'temp_{profile_name}'
        )
        await event.reply(
            f"Профиль {profile_name} активирован на {event.text}",
            buttons=await get_profiles_keyboard()
        )

    del STATES[event.sender_id]

@bot_client.on(events.NewMessage(func=lambda e: True))
async def get_emoji_status_handler(event):
    if not is_owner(event):
        return
    
    if event.forward:
        try:
            sender = await event.get_sender()
            if hasattr(sender, 'emoji_status') and sender.emoji_status:
                document_id = sender.emoji_status.document_id
                await event.reply(f"ID эмодзи-статуса: {document_id}")
        except Exception as e:
            logging.error(f"Ошибка при получении эмодзи-статуса: {e}")

@bot_client.on(events.NewMessage(func=lambda e: e.text == "🔄 Включить постоянно"))
async def activate_profile_permanent(event):
    if not is_owner(event):
        return

    if event.sender_id not in STATES or "profile_name" not in STATES[event.sender_id]:
        await event.reply("Сначала выберите профиль", buttons=await get_profiles_keyboard())
        return

    profile_name = STATES[event.sender_id]["profile_name"]
    
    # Удаляем все временные задачи для этого профиля
    for job in scheduler.get_jobs():
        if job.args and job.args[0] == profile_name and job.id.startswith('temp_'):
            job.remove()
    
    result = await change_profile(profile_name)
    del STATES[event.sender_id]
    
    await event.reply(
        f"{result}. Профиль будет активен постоянно.",
        buttons=await get_profiles_keyboard()
    )
    raise events.StopPropagation()

@bot_client.on(events.NewMessage(func=lambda e: e.text == "⏱ Включить на время"))
async def activate_profile_temporary(event):
    if not is_owner(event):
        return

    if event.sender_id not in STATES or "profile_name" not in STATES[event.sender_id]:
        await event.reply("Сначала выберите профиль", buttons=await get_profiles_keyboard())
        return

    STATES[event.sender_id]["state"] = "waiting_duration"
    
    await event.reply(
        "Выберите длительность:",
        buttons=await get_duration_keyboard()
    )
    raise events.StopPropagation()

@bot_client.on(events.NewMessage(func=lambda e: e.text == "📅 Включить до расписания"))
async def activate_profile_until_schedule(event):
    if not is_owner(event):
        return

    if event.sender_id not in STATES or "profile_name" not in STATES[event.sender_id]:
        await event.reply("Сначала выберите профиль", buttons=await get_profiles_keyboard())
        return

    profile_name = STATES[event.sender_id]["profile_name"]
    
    # Находим следующую запланированную смену профиля
    next_job = None
    next_run_time = None
    for job in scheduler.get_jobs():
        if not job.id.startswith('temp_'):  # Пропускаем временные задачи
            if next_run_time is None or job.next_run_time < next_run_time:
                next_job = job
                next_run_time = job.next_run_time

    # Активируем профиль
    result = await change_profile(profile_name)
    
    if next_run_time is None:
        await event.reply(
            f"{result}\nНет активных расписаний. Профиль будет активен постоянно.",
            buttons=await get_profiles_keyboard()
        )
    else:
        next_change = next_run_time.strftime("%H:%M")
        next_profile = next_job.args[0] if next_job.args else "неизвестный профиль"
        
        await event.reply(
            f"{result}\nПрофиль будет активен до {next_change} "
            f"(следующая автоматическая смена на {next_profile})",
            buttons=await get_profiles_keyboard()
        )
    
    del STATES[event.sender_id]
    raise events.StopPropagation()

@bot_client.on(events.NewMessage(func=lambda e: e.text == "✏️ Редактировать"))
async def edit_profile_start(event):
    if not is_owner(event):
        return

    if event.sender_id not in STATES or "profile_name" not in STATES[event.sender_id]:
        await event.reply("Сначала выберите профиль", buttons=await get_profiles_keyboard())
        return

    profile_name = STATES[event.sender_id]["profile_name"]
    STATES[event.sender_id] = {
        "state": "waiting_first_name",
        "profile_name": profile_name
    }
    
    await event.reply(
        f"Редактирование профиля {profile_name}\nВведите новое имя:",
        buttons=[[Button.text("◀️ Отмена")]]
    )
    raise events.StopPropagation()

@bot_client.on(events.NewMessage(func=lambda e: e.text == "❌ Удалить"))
async def delete_profile(event):
    if not is_owner(event):
        return

    if event.sender_id not in STATES or "profile_name" not in STATES[event.sender_id]:
        await event.reply("Сначала выберите профиль", buttons=await get_profiles_keyboard())
        return

    profile_name = STATES[event.sender_id]["profile_name"]
    
    # Удаляем все задачи для этого профиля
    for job in scheduler.get_jobs():
        if job.args and job.args[0] == profile_name:
            job.remove()
    
    # Удаляем профиль
    if profile_name in PRESET_PROFILES:
        del PRESET_PROFILES[profile_name]
        save_profiles(PRESET_PROFILES)
        
        await event.reply(
            f"Профиль {profile_name} удален!",
            buttons=await get_profiles_keyboard()
        )
    else:
        await event.reply(
            "Профиль не найден!",
            buttons=await get_profiles_keyboard()
        )
    
    del STATES[event.sender_id]
    raise events.StopPropagation()

async def main(debug_mode=False):
    setup_logging(debug_mode)
    scheduler.start()
    
    # Запускаем пользовательский клиент
    print("Подключение пользовательского аккаунта...")
    await user_client.connect()
    
    if not await user_client.is_user_authorized():
        print("Для работы бота требуется авторизация в вашем аккаунте Telegram.")
        print("Пожалуйста, введите номер телефона и код подтверждения.")
        try:
            await user_client.start()
        except Exception as e:
            logging.error(f"Ошибка при авторизации: {e}", exc_info=True)
            await user_client.disconnect()
            return
            
        if not await user_client.is_user_authorized():
            logging.error("Ошибка авторизации пользовательского аккаунта!")
            await user_client.disconnect()
            return
        
        print("Пользовательский аккаунт успешно авторизован!")
    else:
        print("Пользовательский аккаунт подключен!")

    # Запускаем бота
    await bot_client.start(bot_token=BOT_TOKEN)
    print(f"Бот запущен и готов к работе! ID владельца: {OWNER_ID}")
    
    try:
        # Запускаем оба клиента одновременно
        await asyncio.gather(
            bot_client.run_until_disconnected(),
            user_client.run_until_disconnected()
        )
    except KeyboardInterrupt:
        print("\nЗавершение работы...")
    except Exception as e:
        logging.error("Произошла ошибка:", exc_info=True)
    finally:
        await bot_client.disconnect()
        await user_client.disconnect()

if __name__ == '__main__':
    debug_mode = len(sys.argv) > 1 and sys.argv[1].lower() in ['debug', '--debug', '-d']
    asyncio.run(main(debug_mode)) 