import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import logging
from pathlib import Path

class TelegramProfileService(win32serviceutil.ServiceFramework):
    _svc_name_ = "TelegramProfileBot"
    _svc_display_name_ = "Telegram Profile Bot Service"
    _svc_description_ = "Служба для управления профилем Telegram"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_alive = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.is_alive = False

    def SvcDoRun(self):
        try:
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )
            
            # Устанавливаем текущую директорию
            os.chdir(str(Path(__file__).parent))
            
            # Запускаем бота
            import asyncio
            from telegram_profile_bot import main
            asyncio.run(main())
            
        except Exception as e:
            servicemanager.LogErrorMsg(f"Ошибка в службе: {str(e)}")
            logging.error("Ошибка в службе:", exc_info=True)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(TelegramProfileService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(TelegramProfileService) 