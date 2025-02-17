import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import asyncio
from pathlib import Path
from telegram_profile_bot import main

class TelegramBotService(win32serviceutil.ServiceFramework):
    _svc_name_ = "TelegramProfileBot"
    _svc_display_name_ = "Telegram Profile Bot Service"
    _svc_description_ = "Сервис для автоматической смены профиля в Telegram"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = False

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False

    def SvcDoRun(self):
        self.running = True
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        # Установка рабочей директории
        os.chdir(str(Path(__file__).parent))
        
        # Запуск бота
        asyncio.run(main())

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(TelegramBotService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(TelegramBotService) 