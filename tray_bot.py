import pystray
from PIL import Image
import asyncio
import threading
import sys
import os
from pathlib import Path
from telegram_profile_bot import main, bot_client, user_client, scheduler

class TrayBot:
    def __init__(self):
        self.loop = None
        self.bot_task = None
        self.is_running = False
        self.icon = None

    def create_menu(self):
        return pystray.Menu(
            pystray.MenuItem("Статус: Работает", lambda: None, enabled=False),
            pystray.MenuItem("Открыть журнал", self.open_log),
            pystray.MenuItem("Перезапустить", self.restart_bot),
            pystray.MenuItem("Выход", self.stop_bot)
        )

    def open_log(self):
        log_file = Path(__file__).parent / "bot.log"
        if sys.platform == "win32":
            os.startfile(str(log_file))
        else:
            print("Открытие журнала поддерживается только в Windows")

    def restart_bot(self):
        if self.is_running:
            self.stop_bot()
        self.start_bot()

    def stop_bot(self):
        if self.is_running:
            self.is_running = False
            # Останавливаем планировщик
            scheduler.shutdown()
            # Останавливаем клиенты
            if not self.loop.is_closed():
                self.loop.call_soon_threadsafe(lambda: asyncio.create_task(self.cleanup()))
            self.icon.stop()

    async def cleanup(self):
        await bot_client.disconnect()
        await user_client.disconnect()

    def run_bot(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.is_running = True
        try:
            self.loop.run_until_complete(main(debug_mode=False))
        except Exception as e:
            print(f"Ошибка в работе бота: {e}")
        finally:
            self.loop.close()

    def start_bot(self):
        if not self.is_running:
            self.bot_task = threading.Thread(target=self.run_bot)
            self.bot_task.daemon = True
            self.bot_task.start()

    def run(self):
        # Создаем иконку
        image = Image.new('RGB', (64, 64), color='blue')
        self.icon = pystray.Icon(
            "telegram_profile_bot",
            image,
            "Telegram Profile Bot",
            self.create_menu()
        )

        # Запускаем бота
        self.start_bot()

        # Запускаем иконку в трее
        self.icon.run()

if __name__ == "__main__":
    tray_bot = TrayBot()
    tray_bot.run() 