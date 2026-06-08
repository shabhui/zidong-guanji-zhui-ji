class NotificationService:
    def __init__(self, tray_service=None, logger=None):
        self._tray_service = tray_service
        self._logger = logger or (lambda message: None)
        self._unavailable_logged = False

    @property
    def available(self):
        return bool(self._tray_service and getattr(self._tray_service, "available", False) and getattr(self._tray_service, "tray", None))

    def show_reminder(self, title, body):
        if not self.available:
            if not self._unavailable_logged:
                self._logger("系统通知不可用：托盘消息尚未就绪")
                self._unavailable_logged = True
            return False
        try:
            self._tray_service.tray.showMessage(title, body, None, 10000)
        except Exception as exc:
            self._logger(f"系统通知不可用：{exc}")
            return False
        return True
