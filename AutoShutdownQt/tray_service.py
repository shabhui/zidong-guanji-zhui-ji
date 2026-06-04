class TrayService:
    def __init__(self, controller, window, tray_factory=None, logger=None, icon_path=None):
        self._controller = controller
        self._window = window
        self._tray_factory = tray_factory
        self._logger = logger or (lambda message: None)
        self._icon_path = icon_path
        self._tray = None
        self._double_click_reason = None
        self.available = False

    @property
    def tray(self):
        return self._tray

    def setup(self):
        try:
            if self._tray_factory is None:
                from PySide6.QtGui import QColor, QIcon, QPixmap
                from PySide6.QtWidgets import QMenu, QSystemTrayIcon
                icon = QIcon(str(self._icon_path)) if self._icon_path else QIcon()
                if icon.isNull() and hasattr(self._window, "windowIcon"):
                    icon = self._window.windowIcon()
                if icon.isNull():
                    pixmap = QPixmap(32, 32)
                    pixmap.fill(QColor("#7C5CFF"))
                    icon = QIcon(pixmap)
                tray = QSystemTrayIcon(icon, None)
                tray.setIcon(icon)
                self._double_click_reason = QSystemTrayIcon.ActivationReason.DoubleClick
                menu = QMenu()
                menu.addAction("显示/隐藏窗口", self.toggle_window)
                menu.addAction("暂停/继续任务", self.pause_or_resume)
                menu.addAction("取消所有任务", self.cancel_all)
                menu.addAction("退出程序", self.quit_app)
                tray.setContextMenu(menu)
                tray.setToolTip("定时关机助手 3.0")
                tray.show()
                self._tray = tray
            else:
                self._tray = self._tray_factory()
                self._double_click_reason = getattr(self._tray, "DoubleClick", 2)
        except Exception as exc:
            self._logger(f"tray unavailable: {exc}")
            self.available = False
            return False
        if self._tray is None:
            self._logger("tray unavailable: no tray object")
            self.available = False
            return False
        if hasattr(self._tray, "activated"):
            self._tray.activated.connect(self._handle_tray_activation)
        self.available = True
        return True

    def _handle_tray_activation(self, reason):
        if reason == self._double_click_reason:
            self.show_window()

    def show_window(self):
        self._window.show()

    def hide_window(self):
        self._window.hide()

    def minimize_to_tray(self):
        if not self.available or self._tray is None:
            self._logger("minimize to tray skipped: tray unavailable")
            return False
        self.hide_window()
        if hasattr(self._tray, "showMessage"):
            self._tray.showMessage("定时关机助手", "已隐藏到右下角小图标，双击小图标可恢复窗口；右键小图标选择“退出程序”可彻底退出。", None, 3000)
        return True

    def toggle_window(self):
        if getattr(self._window, "visible", True):
            self.hide_window()
        else:
            self.show_window()

    def pause_or_resume(self):
        if getattr(self._controller, "schedulingPaused", False):
            self._controller.resumeScheduling()
        else:
            self._controller.pauseScheduling()

    def cancel_all(self):
        self._controller.cancelAllTasks()

    def quit_app(self):
        if hasattr(self._window, "trayCloseRequested"):
            self._window.trayCloseRequested = True
        self._controller.requestQuit()
