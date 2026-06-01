from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer
from datetime import datetime, timedelta


class AppController(QObject):
    remainingTimeChanged = Signal()
    statusChanged = Signal()
    targetInfoChanged = Signal()
    dryRunChanged = Signal()
    forceCloseChanged = Signal()

    POWER_ACTIONS = ["shutdown", "sleep", "hibernate", "restart", "logoff", "lock"]
    ACTION_LABELS = {
        "shutdown": "关机", "sleep": "睡眠", "hibernate": "休眠",
        "restart": "重启", "logoff": "注销", "lock": "锁定",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dry_run = True
        self._selected_action = "shutdown"
        self._status = "ready"
        self._remaining_seconds = 0
        self._target_time_str = ""
        self._force_close = False
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)

    # --- QML Properties ---

    def getDryRun(self): return self._dry_run
    def setDryRun(self, v):
        if self._dry_run != v:
            self._dry_run = v
            self.dryRunChanged.emit()
    dryRun = Property(bool, getDryRun, setDryRun, notify=dryRunChanged)

    def getStatus(self): return self._status
    status = Property(str, getStatus, notify=statusChanged)

    def getRemainingText(self):
        h = self._remaining_seconds // 3600
        m = (self._remaining_seconds % 3600) // 60
        s = self._remaining_seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    remainingText = Property(str, getRemainingText, notify=remainingTimeChanged)

    def getTargetInfo(self): return self._target_time_str
    targetInfo = Property(str, getTargetInfo, notify=targetInfoChanged)

    def getSelectedAction(self): return self._selected_action
    def setSelectedAction(self, v):
        if v in self.POWER_ACTIONS and self._selected_action != v:
            self._selected_action = v
            self.targetInfoChanged.emit()
    selectedAction = Property(str, getSelectedAction, setSelectedAction, notify=targetInfoChanged)

    def getForceClose(self): return self._force_close
    def setForceClose(self, v):
        if self._force_close != v:
            self._force_close = v
            self.forceCloseChanged.emit()
    forceClose = Property(bool, getForceClose, setForceClose, notify=forceCloseChanged)

    def getActionLabel(self): return self.ACTION_LABELS.get(self._selected_action, "")
    actionLabel = Property(str, getActionLabel, notify=targetInfoChanged)

    def getStatusColor(self):
        return {"ready": "#7DFFC4", "running": "#FFD166", "paused": "#B779FF"}.get(self._status, "#7DFFC4")
    statusColor = Property(str, getStatusColor, notify=statusChanged)

    def getRemainingSeconds(self): return self._remaining_seconds
    remainingSeconds = Property(int, getRemainingSeconds, notify=remainingTimeChanged)

    # --- Slots ---

    @Slot(int, int, int)
    def startCountdown(self, hours, minutes, seconds):
        total = hours * 3600 + minutes * 60 + seconds
        if total <= 0:
            return
        self._remaining_seconds = total
        self._status = "running"
        self._target_time_str = ""
        self._timer.start()
        self.statusChanged.emit()
        self.remainingTimeChanged.emit()
        self.targetInfoChanged.emit()

    @Slot(int, int)
    def startFixedTime(self, hour, minute):
        now = datetime.now()
        target = datetime(now.year, now.month, now.day, hour, minute, 0)
        if target <= now:
            target += timedelta(days=1)
        delta = int((target - now).total_seconds())
        if delta <= 0:
            return
        self._remaining_seconds = delta
        self._status = "running"
        self._target_time_str = target.strftime("%Y-%m-%d %H:%M")
        self._timer.start()
        self.statusChanged.emit()
        self.remainingTimeChanged.emit()
        self.targetInfoChanged.emit()

    @Slot()
    def cancel(self):
        self._timer.stop()
        self._remaining_seconds = 0
        self._status = "ready"
        self._target_time_str = ""
        self.statusChanged.emit()
        self.remainingTimeChanged.emit()
        self.targetInfoChanged.emit()

    @Slot()
    def executeNow(self):
        if self._dry_run:
            print(f"[dryRun] Would execute: {self._selected_action} force={self._force_close}")
            return
        self._execute_power_action()

    def _on_tick(self):
        self._remaining_seconds -= 1
        self.remainingTimeChanged.emit()
        if self._remaining_seconds <= 0:
            self._timer.stop()
            self._status = "ready"
            self.statusChanged.emit()
            if self._dry_run:
                print(f"[dryRun] Timer finished, would execute: {self._selected_action}")
            else:
                self._execute_power_action()

    def _execute_power_action(self):
        from power_service import execute_power_action
        execute_power_action(self._selected_action, self._force_close)
