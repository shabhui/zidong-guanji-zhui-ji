class TrayService:
    def __init__(self, controller, window, tray_factory=None, logger=None):
        self._controller = controller
        self._window = window
        self._tray_factory = tray_factory
        self._logger = logger or (lambda message: None)
        self._tray = None
        self.available = False

    def setup(self):
        try:
            if self._tray_factory is None:
                from PySide6.QtGui import QIcon
                from PySide6.QtWidgets import QMenu, QSystemTrayIcon
                tray = QSystemTrayIcon(QIcon(), None)
                menu = QMenu()
                menu.addAction("Show/Hide", self.toggle_window)
                menu.addAction("Pause/Resume scheduling", self.pause_or_resume)
                menu.addAction("Cancel all tasks", self.cancel_all)
                menu.addAction("Quit", self.quit_app)
                tray.setContextMenu(menu)
                tray.setToolTip("AutoShutdownQt 2.1")
                tray.show()
                self._tray = tray
            else:
                self._tray = self._tray_factory()
        except Exception as exc:
            self._logger(f"tray unavailable: {exc}")
            self.available = False
            return False
        if self._tray is None:
            self._logger("tray unavailable: no tray object")
            self.available = False
            return False
        self.available = True
        return True

    def show_window(self):
        self._window.show()

    def hide_window(self):
        self._window.hide()

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
        self._controller.requestQuit()
