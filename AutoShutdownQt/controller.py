from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer
from datetime import datetime, timedelta
import subprocess

from script_service import run_script


class AppController(QObject):
    remainingTimeChanged = Signal()
    statusChanged = Signal()
    targetInfoChanged = Signal()
    dryRunChanged = Signal()
    forceCloseChanged = Signal()
    scriptConfigChanged = Signal()
    processTriggerChanged = Signal()
    logTextChanged = Signal()

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
        self._script_enabled = False
        self._script_path = ""
        self._script_timeout_seconds = 10
        self._process_name = ""
        self._process_poll_seconds = 5
        self._process_trigger_active = False
        self._process_trigger_status = "未启动"
        self._process_seen = False
        self._logs = ["READY · Dry-run 已开启"]
        self._script_runner = run_script
        self._power_executor = None
        self._process_checker = self._is_process_running
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)
        self._process_timer = QTimer(self)
        self._process_timer.timeout.connect(self._poll_process_trigger)

    # --- QML Properties ---

    def getDryRun(self): return self._dry_run
    def setDryRun(self, v):
        v = bool(v)
        if self._dry_run != v:
            self._dry_run = v
            self._add_log("Dry-run 已开启" if v else "真实执行模式已开启")
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
            self._add_log(f"已选择动作：{self.ACTION_LABELS.get(v, v)}")
            self.targetInfoChanged.emit()
    selectedAction = Property(str, getSelectedAction, setSelectedAction, notify=targetInfoChanged)

    def getForceClose(self): return self._force_close
    def setForceClose(self, v):
        v = bool(v)
        if self._force_close != v:
            self._force_close = v
            self._add_log("强制关闭已开启" if v else "强制关闭已关闭")
            self.forceCloseChanged.emit()
    forceClose = Property(bool, getForceClose, setForceClose, notify=forceCloseChanged)

    def getActionLabel(self): return self.ACTION_LABELS.get(self._selected_action, "")
    actionLabel = Property(str, getActionLabel, notify=targetInfoChanged)

    def getStatusColor(self):
        return {"ready": "#7DFFC4", "running": "#FFD166", "paused": "#B779FF"}.get(self._status, "#7DFFC4")
    statusColor = Property(str, getStatusColor, notify=statusChanged)

    def getRemainingSeconds(self): return self._remaining_seconds
    remainingSeconds = Property(int, getRemainingSeconds, notify=remainingTimeChanged)

    def getScriptEnabled(self): return self._script_enabled
    def setScriptEnabled(self, v):
        v = bool(v)
        if self._script_enabled != v:
            self._script_enabled = v
            self._add_log("执行前脚本已启用" if v else "执行前脚本已关闭")
            self.scriptConfigChanged.emit()
    scriptEnabled = Property(bool, getScriptEnabled, setScriptEnabled, notify=scriptConfigChanged)

    def getScriptPath(self): return self._script_path
    def setScriptPath(self, v):
        v = str(v or "")
        if self._script_path != v:
            self._script_path = v
            self.scriptConfigChanged.emit()
    scriptPath = Property(str, getScriptPath, setScriptPath, notify=scriptConfigChanged)

    def getScriptTimeoutSeconds(self): return self._script_timeout_seconds
    def setScriptTimeoutSeconds(self, v):
        try:
            v = max(1, int(v))
        except (TypeError, ValueError):
            v = 10
        if self._script_timeout_seconds != v:
            self._script_timeout_seconds = v
            self.scriptConfigChanged.emit()
    scriptTimeoutSeconds = Property(int, getScriptTimeoutSeconds, setScriptTimeoutSeconds, notify=scriptConfigChanged)

    def getProcessName(self): return self._process_name
    def setProcessName(self, v):
        v = str(v or "")
        if self._process_name != v:
            self._process_name = v
            self.processTriggerChanged.emit()
    processName = Property(str, getProcessName, setProcessName, notify=processTriggerChanged)

    def getProcessPollSeconds(self): return self._process_poll_seconds
    def setProcessPollSeconds(self, v):
        try:
            v = max(1, int(v))
        except (TypeError, ValueError):
            v = 5
        if self._process_poll_seconds != v:
            self._process_poll_seconds = v
            if self._process_trigger_active:
                self._process_timer.setInterval(v * 1000)
            self.processTriggerChanged.emit()
    processPollSeconds = Property(int, getProcessPollSeconds, setProcessPollSeconds, notify=processTriggerChanged)

    def getProcessTriggerActive(self): return self._process_trigger_active
    processTriggerActive = Property(bool, getProcessTriggerActive, notify=processTriggerChanged)

    def getProcessTriggerStatus(self): return self._process_trigger_status
    processTriggerStatus = Property(str, getProcessTriggerStatus, notify=processTriggerChanged)

    def getLogText(self): return "\n".join(self._logs[-8:])
    logText = Property(str, getLogText, notify=logTextChanged)

    # --- Slots ---

    @Slot(int, int, int)
    def startCountdown(self, hours, minutes, seconds):
        total = hours * 3600 + minutes * 60 + seconds
        if total <= 0:
            self._add_log("倒计时时长无效，已忽略")
            return
        self._remaining_seconds = total
        self._status = "running"
        self._target_time_str = ""
        self._timer.start()
        self._add_log(f"已启动倒计时：{self._format_duration(total)} 后执行 {self.actionLabel}")
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
            self._add_log("指定时间无效，已忽略")
            return
        self._remaining_seconds = delta
        self._status = "running"
        self._target_time_str = target.strftime("%Y-%m-%d %H:%M")
        self._timer.start()
        self._add_log(f"已启动定时：{self._target_time_str} 执行 {self.actionLabel}")
        self.statusChanged.emit()
        self.remainingTimeChanged.emit()
        self.targetInfoChanged.emit()

    @Slot(str)
    def applyTaskTemplate(self, key):
        templates = {
            "shutdown_15": ("shutdown", "15 分钟后关机", "countdown", (0, 15, 0)),
            "shutdown_30": ("shutdown", "30 分钟后关机", "countdown", (0, 30, 0)),
            "sleep_60": ("sleep", "1 小时后睡眠", "countdown", (1, 0, 0)),
            "shutdown_2300": ("shutdown", "今晚 23:00 关机", "fixed", (23, 0)),
        }
        template = templates.get(key)
        if not template:
            self._add_log(f"未知任务模板：{key}")
            return
        action, label, mode, args = template
        self._selected_action = action
        self.targetInfoChanged.emit()
        self._add_log(f"应用任务模板：{label}")
        if mode == "countdown":
            self.startCountdown(*args)
        else:
            self.startFixedTime(*args)

    @Slot()
    def cancel(self):
        self._timer.stop()
        self._remaining_seconds = 0
        self._status = "ready"
        self._target_time_str = ""
        self._add_log("已取消当前任务")
        self.statusChanged.emit()
        self.remainingTimeChanged.emit()
        self.targetInfoChanged.emit()

    @Slot()
    def testScript(self):
        if not self._script_enabled:
            self._add_log("执行前脚本未启用")
            return
        if self._dry_run:
            self._add_log(f"Dry-run：将执行脚本 {self._script_path or '(未设置路径)'}")
            return
        result = self._script_runner(self._script_path, self._script_timeout_seconds)
        self._add_log(result.message)

    @Slot()
    def startProcessTrigger(self):
        name = self._process_name.strip()
        if not name:
            self._process_trigger_active = False
            self._process_trigger_status = "请输入进程名"
            self._add_log("进程退出触发未启动：请输入进程名")
            self.processTriggerChanged.emit()
            return
        self._process_trigger_active = True
        self._process_seen = bool(self._process_checker(name))
        if self._process_seen:
            self._process_trigger_status = f"监控中：{name}"
            self._add_log(f"进程退出触发已启动：正在监控 {name}")
        else:
            self._process_trigger_status = f"等待进程出现：{name}"
            self._add_log(f"进程退出触发已启动：等待进程出现 {name}")
        self._process_timer.setInterval(self._process_poll_seconds * 1000)
        self._process_timer.start()
        self.processTriggerChanged.emit()

    @Slot()
    def stopProcessTrigger(self):
        self._process_timer.stop()
        self._process_trigger_active = False
        self._process_seen = False
        self._process_trigger_status = "已停止"
        self._add_log("进程退出触发已停止")
        self.processTriggerChanged.emit()

    @Slot()
    def executeNow(self):
        self._execute_with_script("立即执行")

    def _on_tick(self):
        self._remaining_seconds -= 1
        self.remainingTimeChanged.emit()
        if self._remaining_seconds <= 0:
            self._timer.stop()
            self._status = "ready"
            self.statusChanged.emit()
            self._execute_with_script("倒计时结束")

    def _execute_with_script(self, reason):
        if self._script_enabled:
            if self._dry_run:
                self._add_log(f"Dry-run：将执行脚本 {self._script_path or '(未设置路径)'}")
            else:
                result = self._script_runner(self._script_path, self._script_timeout_seconds)
                self._add_log(result.message)
                if not result.ok:
                    self._add_log("脚本失败，已阻止电源动作")
                    return
        if self._dry_run:
            message = f"[dryRun] Would execute: {self._selected_action} force={self._force_close}"
            print(message)
            self._add_log(message)
            return
        self._add_log(f"{reason}：执行 {self.actionLabel}")
        self._execute_power_action()

    def _poll_process_trigger(self):
        if not self._process_trigger_active:
            return
        name = self._process_name.strip()
        running = bool(self._process_checker(name))
        if running:
            if not self._process_seen:
                self._add_log(f"已发现进程：{name}")
            self._process_seen = True
            self._process_trigger_status = f"监控中：{name}"
            self.processTriggerChanged.emit()
            return
        if self._process_seen:
            self._process_timer.stop()
            self._process_trigger_active = False
            self._process_seen = False
            self._process_trigger_status = f"进程已退出：{name}"
            self._add_log(f"进程已退出：{name}")
            self.processTriggerChanged.emit()
            self._execute_with_script("进程退出触发")
        else:
            self._process_trigger_status = f"等待进程出现：{name}"
            self.processTriggerChanged.emit()

    def _execute_power_action(self):
        if self._power_executor:
            self._power_executor(self._selected_action, self._force_close)
            return
        from power_service import execute_power_action
        execute_power_action(self._selected_action, self._force_close)

    def _is_process_running(self, process_name):
        clean_name = (process_name or "").strip().lower()
        if not clean_name:
            return False
        try:
            completed = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=4,
                check=False,
            )
        except Exception:
            return False
        return any(line.lower().startswith(f'"{clean_name}"') for line in completed.stdout.splitlines())

    def _add_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._logs.append(f"{timestamp} · {message}")
        self._logs = self._logs[-24:]
        self.logTextChanged.emit()

    def _format_duration(self, seconds):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        parts = []
        if h:
            parts.append(f"{h} 小时")
        if m:
            parts.append(f"{m} 分钟")
        if s:
            parts.append(f"{s} 秒")
        return " ".join(parts) or "0 秒"
