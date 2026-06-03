from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer, QCoreApplication
from datetime import datetime, timedelta
from pathlib import Path
import json
import math
import os
import subprocess
import sys

from network_service import NetworkReader, compute_speed
from script_service import run_script
from settings_service import default_settings, load_settings, log_export_path as default_log_export_path, save_settings
from task_model import RepeatRule, TaskTriggerType
from task_scheduler import TaskScheduler


class AppController(QObject):
    remainingTimeChanged = Signal()
    statusChanged = Signal()
    targetInfoChanged = Signal()
    dryRunChanged = Signal()
    forceCloseChanged = Signal()
    scriptConfigChanged = Signal()
    processTriggerChanged = Signal()
    networkTriggerChanged = Signal()
    logTextChanged = Signal()
    taskQueueChanged = Signal()
    schedulingPausedChanged = Signal()

    POWER_ACTIONS = ["shutdown", "sleep", "hibernate", "restart", "logoff", "lock"]
    ACTION_LABELS = {
        "shutdown": "关机", "sleep": "睡眠", "hibernate": "休眠",
        "restart": "重启", "logoff": "注销", "lock": "锁定",
    }

    def __init__(self, parent=None, settings_path=None, network_reader=None, log_export_path=None, open_folder=None):
        super().__init__(parent)
        self._settings_path = settings_path
        self._persist_settings = self._should_persist_settings(settings_path)
        settings = load_settings(settings_path) if self._persist_settings else default_settings()

        self._dry_run = self._coerce_bool(settings.get("dryRun"), True)
        self._selected_action = self._coerce_action(settings.get("selectedAction"), "shutdown")
        self._status = "ready"
        self._remaining_seconds = 0
        self._target_time_str = ""
        self._force_close = self._coerce_bool(settings.get("forceClose"), False)
        self._script_enabled = self._coerce_bool(settings.get("scriptEnabled"), False)
        self._script_path = str(settings.get("scriptPath") or "")
        self._script_timeout_seconds = self._coerce_int(settings.get("scriptTimeoutSeconds"), 10, minimum=1)
        self._process_name = str(settings.get("processName") or "")
        self._process_poll_seconds = self._coerce_int(settings.get("processPollSeconds"), 5, minimum=1)
        self._process_trigger_active = False
        self._process_trigger_status = "未启动"
        self._process_seen = False
        self._process_target_name = ""
        self._network_download_threshold_kbps = self._coerce_float(settings.get("networkDownloadThresholdKbps"), 10.0, minimum=0.0)
        self._network_upload_threshold_kbps = self._coerce_float(settings.get("networkUploadThresholdKbps"), 10.0, minimum=0.0)
        self._network_idle_seconds = self._coerce_int(settings.get("networkIdleSeconds"), 60, minimum=1)
        self._network_poll_seconds = self._coerce_int(settings.get("networkPollSeconds"), 3, minimum=1)
        self._network_trigger_active = False
        self._network_trigger_status = "未启动"
        self._network_speed_text = "等待网络监控"
        self._network_previous_sample = None
        self._network_idle_elapsed = 0.0
        self._logs = ["READY · Dry-run 已开启" if self._dry_run else "READY · 真实执行模式"]
        self._script_runner = run_script
        self._power_executor = None
        self._process_checker = self._is_process_running
        self._last_process_check_error = ""
        self._network_reader = network_reader or NetworkReader()
        self._scheduler = TaskScheduler(now_provider=self._now, diagnostic_logger=self._add_log)
        self._scheduler.load_from_settings(settings.get("taskQueue"))
        self._log_export_path = log_export_path
        self._open_folder = open_folder
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)
        self._process_timer = QTimer(self)
        self._process_timer.timeout.connect(self._poll_process_trigger)
        self._network_timer = QTimer(self)
        self._network_timer.timeout.connect(self._poll_network_trigger)
        self._tray_service = None

    # --- QML Properties ---

    def getDryRun(self): return self._dry_run
    def setDryRun(self, v):
        v = bool(v)
        if self._dry_run != v:
            self._dry_run = v
            self._add_log("Dry-run 已开启" if v else "真实执行模式已开启")
            self._save_settings()
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
            self._save_settings()
            self.targetInfoChanged.emit()
    selectedAction = Property(str, getSelectedAction, setSelectedAction, notify=targetInfoChanged)

    def getForceClose(self): return self._force_close
    def setForceClose(self, v):
        v = bool(v)
        if self._force_close != v:
            self._force_close = v
            self._add_log("强制关闭已开启" if v else "强制关闭已关闭")
            self._save_settings()
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
            self._save_settings()
            self.scriptConfigChanged.emit()
    scriptEnabled = Property(bool, getScriptEnabled, setScriptEnabled, notify=scriptConfigChanged)

    def getScriptPath(self): return self._script_path
    def setScriptPath(self, v):
        v = str(v or "")
        if self._script_path != v:
            self._script_path = v
            self._save_settings()
            self.scriptConfigChanged.emit()
    scriptPath = Property(str, getScriptPath, setScriptPath, notify=scriptConfigChanged)

    def getScriptTimeoutSeconds(self): return self._script_timeout_seconds
    def setScriptTimeoutSeconds(self, v):
        v = self._coerce_int(v, 10, minimum=1)
        if self._script_timeout_seconds != v:
            self._script_timeout_seconds = v
            self._save_settings()
            self.scriptConfigChanged.emit()
    scriptTimeoutSeconds = Property(int, getScriptTimeoutSeconds, setScriptTimeoutSeconds, notify=scriptConfigChanged)

    def getProcessName(self): return self._process_name
    def setProcessName(self, v):
        v = str(v or "")
        if self._process_name != v:
            self._process_name = v
            self._save_settings()
            self.processTriggerChanged.emit()
    processName = Property(str, getProcessName, setProcessName, notify=processTriggerChanged)

    def getProcessPollSeconds(self): return self._process_poll_seconds
    def setProcessPollSeconds(self, v):
        v = self._coerce_int(v, 5, minimum=1)
        if self._process_poll_seconds != v:
            self._process_poll_seconds = v
            if self._process_trigger_active:
                self._process_timer.setInterval(v * 1000)
            self._save_settings()
            self.processTriggerChanged.emit()
    processPollSeconds = Property(int, getProcessPollSeconds, setProcessPollSeconds, notify=processTriggerChanged)

    def getProcessTriggerActive(self): return self._process_trigger_active
    processTriggerActive = Property(bool, getProcessTriggerActive, notify=processTriggerChanged)

    def getProcessTriggerStatus(self): return self._process_trigger_status
    processTriggerStatus = Property(str, getProcessTriggerStatus, notify=processTriggerChanged)

    def getNetworkDownloadThresholdKbps(self): return self._network_download_threshold_kbps
    def setNetworkDownloadThresholdKbps(self, v):
        v = self._coerce_float(v, 10.0, minimum=0.0)
        if self._network_download_threshold_kbps != v:
            self._network_download_threshold_kbps = v
            self._save_settings()
            self.networkTriggerChanged.emit()
    networkDownloadThresholdKbps = Property(float, getNetworkDownloadThresholdKbps, setNetworkDownloadThresholdKbps, notify=networkTriggerChanged)

    def getNetworkUploadThresholdKbps(self): return self._network_upload_threshold_kbps
    def setNetworkUploadThresholdKbps(self, v):
        v = self._coerce_float(v, 10.0, minimum=0.0)
        if self._network_upload_threshold_kbps != v:
            self._network_upload_threshold_kbps = v
            self._save_settings()
            self.networkTriggerChanged.emit()
    networkUploadThresholdKbps = Property(float, getNetworkUploadThresholdKbps, setNetworkUploadThresholdKbps, notify=networkTriggerChanged)

    def getNetworkIdleSeconds(self): return self._network_idle_seconds
    def setNetworkIdleSeconds(self, v):
        v = self._coerce_int(v, 60, minimum=1)
        if self._network_idle_seconds != v:
            self._network_idle_seconds = v
            self._save_settings()
            self.networkTriggerChanged.emit()
    networkIdleSeconds = Property(int, getNetworkIdleSeconds, setNetworkIdleSeconds, notify=networkTriggerChanged)

    def getNetworkPollSeconds(self): return self._network_poll_seconds
    def setNetworkPollSeconds(self, v):
        v = self._coerce_int(v, 3, minimum=1)
        if self._network_poll_seconds != v:
            self._network_poll_seconds = v
            if self._network_trigger_active:
                self._network_timer.setInterval(v * 1000)
            self._save_settings()
            self.networkTriggerChanged.emit()
    networkPollSeconds = Property(int, getNetworkPollSeconds, setNetworkPollSeconds, notify=networkTriggerChanged)

    def getNetworkTriggerActive(self): return self._network_trigger_active
    networkTriggerActive = Property(bool, getNetworkTriggerActive, notify=networkTriggerChanged)

    def getNetworkTriggerStatus(self): return self._network_trigger_status
    networkTriggerStatus = Property(str, getNetworkTriggerStatus, notify=networkTriggerChanged)

    def getNetworkSpeedText(self): return self._network_speed_text
    networkSpeedText = Property(str, getNetworkSpeedText, notify=networkTriggerChanged)

    def getLogText(self): return "\n".join(self._logs[-8:])
    logText = Property(str, getLogText, notify=logTextChanged)

    def getDiagnosticText(self):
        return self._diagnostic_text()
    diagnosticText = Property(str, getDiagnosticText, notify=logTextChanged)

    def getQueueTaskCount(self):
        return len(self._scheduler.tasks)
    queueTaskCount = Property(int, getQueueTaskCount, notify=taskQueueChanged)

    def getQueueText(self):
        rows = self._scheduler.rows()
        if not rows:
            return "暂无任务"
        return "\n".join(
            f"{row['name']} · {row['triggerSummary']} · {row['repeatSummary']} · {row['status']} · {row['nextRunText']}"
            for row in rows
        )
    queueText = Property(str, getQueueText, notify=taskQueueChanged)

    def getQueueRowsJson(self):
        return json.dumps(self._scheduler.rows(), ensure_ascii=False)
    queueRowsJson = Property(str, getQueueRowsJson, notify=taskQueueChanged)

    def getSchedulingPaused(self):
        return self._scheduler.paused
    schedulingPaused = Property(bool, getSchedulingPaused, notify=schedulingPausedChanged)

    def getTrayService(self):
        return self._tray_service

    def setTrayService(self, service):
        self._tray_service = service
    trayService = property(getTrayService, setTrayService)

    # --- Slots ---

    @Slot(int, int, int)
    def startCountdown(self, hours, minutes, seconds):
        total = hours * 3600 + minutes * 60 + seconds
        if total <= 0:
            self._add_log("倒计时时长无效，已忽略")
            return
        task = self._scheduler.add_task(
            f"倒计时 {self._format_duration(total)}",
            self._selected_action,
            self._force_close,
            TaskTriggerType.COUNTDOWN,
            {"seconds": total},
            RepeatRule.ONCE,
        )
        self._save_settings()
        self._timer.start()
        self._add_log(f"已加入任务队列：{task.name} 后执行 {self.actionLabel}")
        self.taskQueueChanged.emit()

    @Slot(int, int)
    def startFixedTime(self, hour, minute):
        self.addFixedTimeTask(f"固定时间 {hour:02d}:{minute:02d}", hour, minute, RepeatRule.ONCE.value)

    @Slot(str, int, int, str)
    def addFixedTimeTask(self, name, hour, minute, repeat_rule):
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            self._add_log("指定时间无效，已忽略")
            return
        try:
            rule = RepeatRule(repeat_rule)
        except ValueError:
            self._add_log("重复规则无效，已忽略")
            return
        task = self._scheduler.add_task(
            name or f"固定时间 {hour:02d}:{minute:02d}",
            self._selected_action,
            self._force_close,
            TaskTriggerType.FIXED_TIME,
            {"hour": hour, "minute": minute},
            rule,
        )
        self._save_settings()
        self._timer.start()
        self._add_log(f"已加入任务队列：{task.name} 执行 {self.actionLabel}")
        self.taskQueueChanged.emit()

    @Slot()
    def pauseScheduling(self):
        self._scheduler.pause()
        self._add_log("调度已暂停")
        self.schedulingPausedChanged.emit()
        self.taskQueueChanged.emit()

    @Slot()
    def resumeScheduling(self):
        self._scheduler.resume()
        self._add_log("调度已恢复")
        self.schedulingPausedChanged.emit()
        self.taskQueueChanged.emit()

    @Slot()
    def cancelAllTasks(self):
        for task in list(self._scheduler.tasks):
            self._scheduler.remove_task(task.id)
        self.cancel()
        self._save_settings()
        self._add_log("已取消所有任务")
        self.taskQueueChanged.emit()

    @Slot()
    def requestQuit(self):
        active = [task for task in self._scheduler.tasks if task.enabled]
        if active:
            self._add_log("退出前请确认：仍有启用任务")
        QCoreApplication.quit()

    @Slot(str, bool)
    def setQueueTaskEnabled(self, task_id, enabled):
        try:
            self._scheduler.set_enabled(task_id, enabled)
        except KeyError:
            self._add_log(f"任务不存在：{task_id}")
            return
        self._save_settings()
        self._add_log("任务已启用" if enabled else "任务已禁用")
        self.taskQueueChanged.emit()

    @Slot(str)
    def deleteQueueTask(self, task_id):
        try:
            task = self._scheduler.get_task(task_id)
        except KeyError:
            self._add_log(f"任务不存在：{task_id}")
            return
        if task.trigger_type == TaskTriggerType.PROCESS_EXIT:
            self._stop_process_monitor_without_queue_update()
            self.processTriggerChanged.emit()
        elif task.trigger_type == TaskTriggerType.NETWORK_IDLE:
            self._stop_network_monitor_without_queue_update()
            self.networkTriggerChanged.emit()
        self._scheduler.remove_task(task_id)
        self._save_settings()
        self._add_log("任务已删除")
        self.taskQueueChanged.emit()

    @Slot(str)
    def runQueueTaskDryRunCheck(self, task_id):
        try:
            task = self._scheduler.get_task(task_id)
        except KeyError:
            self._add_log(f"任务不存在：{task_id}")
            return
        self._add_log(f"Dry-run 检查：{task.name} -> {task.action} force={task.force_close}")

    @Slot(str)
    def applyTaskTemplate(self, key):
        templates = {
            "shutdown_15": ("shutdown", "15 分钟后关机", "countdown", (0, 15, 0)),
            "shutdown_30": ("shutdown", "30 分钟后关机", "countdown", (0, 30, 0)),
            "sleep_60": ("sleep", "1 小时后睡眠", "countdown", (1, 0, 0)),
            "shutdown_2300": ("shutdown", "今晚 23:00 关机", "fixed", (23, 0)),
            "lock_5": ("lock", "5 分钟后锁定", "countdown", (0, 5, 0)),
            "sleep_10": ("sleep", "10 分钟后睡眠", "countdown", (0, 10, 0)),
            "shutdown_midnight": ("shutdown", "明天 00:00 关机", "fixed", (0, 0)),
        }
        template = templates.get(key)
        if not template:
            self._add_log(f"未知任务模板：{key}")
            return
        action, label, mode, args = template
        self._selected_action = action
        self._save_settings()
        self.targetInfoChanged.emit()
        self._add_log(f"应用任务模板：{label}")
        if mode == "countdown":
            self.startCountdown(*args)
        else:
            self.startFixedTime(*args)

    @Slot(bool)
    def requestDryRunChange(self, enabled):
        self.dryRun = bool(enabled)
        if not self._dry_run:
            self._add_log("真实执行模式已开启：请确认动作、触发器、脚本路径和未保存工作")

    @Slot(int)
    def snoozeMinutes(self, minutes):
        minutes = self._coerce_int(minutes, 0, minimum=0)
        if minutes <= 0:
            self._add_log("延后时长无效，已忽略")
            return
        if self._status != "running" or not self._timer.isActive():
            self._add_log("没有正在运行的定时任务，无法延后")
            return
        self._remaining_seconds += minutes * 60
        self._target_time_str = ""
        self._add_log(f"已延后 {minutes} 分钟")
        self.remainingTimeChanged.emit()
        self.targetInfoChanged.emit()

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
        script_path = self._validate_script_before_real_execution()
        if not script_path:
            return
        result = self._script_runner(script_path, self._script_timeout_seconds)
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
        self._process_target_name = name
        self._process_seen = self._check_process_running(name)
        if self._last_process_check_error:
            self._process_trigger_active = False
            self._process_seen = False
            self._process_target_name = ""
            self._process_trigger_status = f"进程检测失败：{self._last_process_check_error}"
            self._add_log(f"进程退出触发未启动：{self._process_trigger_status}")
            self.processTriggerChanged.emit()
            return
        if self._process_seen:
            self._process_trigger_status = f"监控中：{name}"
            self._add_log(f"进程退出触发已启动：正在监控 {name}")
        else:
            self._process_trigger_status = f"等待进程出现：{name}"
            self._add_log(f"进程退出触发已启动：等待进程出现 {name}")
        self._process_timer.setInterval(self._process_poll_seconds * 1000)
        self._process_timer.start()
        if self._remove_queue_tasks_by_trigger(TaskTriggerType.PROCESS_EXIT):
            self._add_log("已替换上一进程退出队列任务")
        self._scheduler.add_task(
            f"进程退出：{name}",
            self._selected_action,
            self._force_close,
            TaskTriggerType.PROCESS_EXIT,
            {"processName": name, "pollSeconds": self._process_poll_seconds},
            RepeatRule.ONCE,
        )
        self._save_settings()
        self.taskQueueChanged.emit()
        self.processTriggerChanged.emit()

    @Slot()
    def stopProcessTrigger(self):
        self._stop_process_monitor_without_queue_update()
        self._remove_queue_tasks_by_trigger(TaskTriggerType.PROCESS_EXIT)
        self._save_settings()
        self._add_log("进程退出触发已停止")
        self.taskQueueChanged.emit()
        self.processTriggerChanged.emit()

    @Slot()
    def startNetworkTrigger(self):
        sample = self._network_reader.sample()
        self._network_previous_sample = sample
        self._network_idle_elapsed = 0.0
        self._network_speed_text = "下载 0.0 KB/s · 上传 0.0 KB/s"
        if not sample.available:
            message = sample.message or "network unavailable"
            self._network_trigger_active = False
            self._network_trigger_status = message
            self._add_log(f"网络监控未启动：{message}")
            self.networkTriggerChanged.emit()
            return
        self._network_trigger_active = True
        self._network_trigger_status = f"监控中：0/{self._network_idle_seconds} 秒"
        self._network_timer.setInterval(self._network_poll_seconds * 1000)
        self._network_timer.start()
        if self._remove_queue_tasks_by_trigger(TaskTriggerType.NETWORK_IDLE):
            self._add_log("已替换上一网络闲置队列任务")
        self._scheduler.add_task(
            "网络闲置触发",
            self._selected_action,
            self._force_close,
            TaskTriggerType.NETWORK_IDLE,
            {
                "downloadKbps": self._network_download_threshold_kbps,
                "uploadKbps": self._network_upload_threshold_kbps,
                "idleSeconds": self._network_idle_seconds,
                "pollSeconds": self._network_poll_seconds,
            },
            RepeatRule.ONCE,
        )
        self._save_settings()
        self._add_log("网络闲置触发已启动")
        self.taskQueueChanged.emit()
        self.networkTriggerChanged.emit()

    @Slot()
    def stopNetworkTrigger(self):
        self._stop_network_monitor_without_queue_update()
        self._remove_queue_tasks_by_trigger(TaskTriggerType.NETWORK_IDLE)
        self._save_settings()
        self._add_log("网络闲置触发已停止")
        self.taskQueueChanged.emit()
        self.networkTriggerChanged.emit()

    @Slot()
    def clearLogs(self):
        self._logs = ["READY · 日志已清空"]
        self.logTextChanged.emit()

    @Slot()
    def exportLogs(self):
        target = Path(self._log_export_path) if self._log_export_path is not None else default_log_export_path()
        try:
            target = target.expanduser()
            target.parent.mkdir(parents=True, exist_ok=True)
            content = "=== Diagnostics ===\n" + self._diagnostic_text() + "\n\n=== Recent Logs ===\n" + "\n".join(self._logs) + "\n"
            target.write_text(content, encoding="utf-8")
        except Exception as exc:
            self._add_log(f"日志导出失败：{exc}")
            return
        self._add_log(f"日志已导出：{target}")

    @Slot()
    def exportDiagnostics(self):
        log_target = Path(self._log_export_path) if self._log_export_path is not None else default_log_export_path()
        target = log_target.expanduser().with_name(f"{log_target.stem}-diagnostics{log_target.suffix}")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(self._diagnostic_text() + "\n", encoding="utf-8")
        except Exception as exc:
            self._add_log(f"诊断导出失败：{exc}")
            return
        self._add_log(f"诊断已导出：{target}")

    @Slot()
    def validateScriptPath(self):
        clean_path = self._script_path.strip()
        if not clean_path:
            self._add_log("脚本路径为空")
            return
        path = Path(clean_path).expanduser()
        if path.exists():
            self._add_log(f"脚本路径有效：{path}")
        else:
            self._add_log(f"脚本路径不存在：{path}")

    @Slot()
    def openScriptFolder(self):
        clean_path = self._script_path.strip()
        if not clean_path:
            self._add_log("脚本路径为空，无法打开目录")
            return
        path = Path(clean_path).expanduser()
        if not path.exists():
            self._add_log(f"脚本路径不存在，无法打开目录：{path}")
            return
        folder = path if path.is_dir() else path.parent
        try:
            if self._open_folder:
                self._open_folder(folder)
            else:
                self._open_path(folder)
        except Exception as exc:
            self._add_log(f"打开目录失败：{exc}")
            return
        self._add_log(f"已打开目录：{folder}")

    @Slot()
    def executeNow(self):
        self._execute_with_script("立即执行")

    def _replace_active_timed_task_if_needed(self):
        if self._status == "running" and self._timer.isActive():
            self._timer.stop()
            self._remaining_seconds = 0
            self._target_time_str = ""
            self._add_log("已替换上一任务")

    def _on_tick(self):
        now = self._now()
        due_tasks = self._scheduler.due_tasks(now)
        if due_tasks:
            for task in due_tasks:
                self._execute_task(task, now)
            self._save_settings()
            self.taskQueueChanged.emit()
            return
        if self._remaining_seconds <= 0:
            return
        self._remaining_seconds -= 1
        self.remainingTimeChanged.emit()
        if self._remaining_seconds <= 0:
            self._timer.stop()
            self._status = "ready"
            self.statusChanged.emit()
            self._execute_with_script("倒计时结束")

    def _queue_tasks_by_trigger(self, trigger_type):
        return [task for task in self._scheduler.tasks if task.trigger_type == trigger_type]

    def _remove_queue_tasks_by_trigger(self, trigger_type):
        removed = False
        for task in self._queue_tasks_by_trigger(trigger_type):
            removed = self._scheduler.remove_task(task.id) or removed
        return removed

    def _stop_process_monitor_without_queue_update(self):
        self._process_timer.stop()
        self._process_trigger_active = False
        self._process_seen = False
        self._process_target_name = ""
        self._process_trigger_status = "已停止"

    def _stop_network_monitor_without_queue_update(self):
        self._network_timer.stop()
        self._network_trigger_active = False
        self._network_idle_elapsed = 0.0
        self._network_previous_sample = None
        self._network_trigger_status = "已停止"

    def _execute_task(self, task, now):
        previous_action = self._selected_action
        previous_force_close = self._force_close
        self._selected_action = task.action
        self._force_close = task.force_close
        try:
            self._execute_with_script(f"任务队列触发：{task.name}")
            self._scheduler.mark_executed(task.id, now, success=True)
        except Exception as exc:
            self._scheduler.mark_executed(task.id, now, success=False, error=exc)
            self._add_log(f"任务执行失败：{task.name}：{exc}")
        finally:
            self._selected_action = previous_action
            self._force_close = previous_force_close

    def _validate_script_before_real_execution(self):
        clean_path = self._script_path.strip()
        if not clean_path:
            self._add_log("脚本路径为空，已阻止电源动作")
            return None
        path = Path(clean_path).expanduser()
        if not path.exists():
            self._add_log(f"脚本路径不存在，已阻止电源动作：{path}")
            return None
        return str(path)

    def _execute_with_script(self, reason):
        if self._script_enabled:
            if self._dry_run:
                self._add_log(f"Dry-run：将执行脚本 {self._script_path or '(未设置路径)'}")
            else:
                script_path = self._validate_script_before_real_execution()
                if not script_path:
                    return
                result = self._script_runner(script_path, self._script_timeout_seconds)
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
        try:
            self._execute_power_action()
        except Exception as exc:
            self._add_log(f"电源动作执行失败：{exc}")

    def _poll_process_trigger(self):
        if not self._process_trigger_active:
            return
        name = self._process_target_name or self._process_name.strip()
        running = self._check_process_running(name)
        if self._last_process_check_error:
            self._process_timer.stop()
            self._process_trigger_active = False
            self._process_seen = False
            self._process_target_name = ""
            self._process_trigger_status = f"进程检测失败：{self._last_process_check_error}"
            self._add_log(f"进程退出触发已停止：{self._process_trigger_status}")
            self.processTriggerChanged.emit()
            return
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
            self._process_target_name = ""
            self._process_trigger_status = f"进程已退出：{name}"
            self._add_log(f"进程已退出：{name}")
            self.processTriggerChanged.emit()
            self._execute_with_script("进程退出触发")
        else:
            self._process_trigger_status = f"等待进程出现：{name}"
            self.processTriggerChanged.emit()

    def _poll_network_trigger(self):
        if not self._network_trigger_active:
            return
        current = self._network_reader.sample()
        speed = compute_speed(self._network_previous_sample, current)
        if not speed.available:
            message = speed.message or current.message or "network unavailable"
            self._network_timer.stop()
            self._network_trigger_active = False
            self._network_trigger_status = message
            self._network_speed_text = "网络计数不可用"
            self._add_log(f"网络监控已停止：{message}")
            self.networkTriggerChanged.emit()
            return

        self._network_previous_sample = current
        self._network_speed_text = f"下载 {speed.download_kbps:.1f} KB/s · 上传 {speed.upload_kbps:.1f} KB/s"
        is_idle = (
            speed.download_kbps < self._network_download_threshold_kbps
            and speed.upload_kbps < self._network_upload_threshold_kbps
        )
        if is_idle:
            self._network_idle_elapsed += speed.elapsed_seconds
            elapsed = min(int(self._network_idle_elapsed), self._network_idle_seconds)
            self._network_trigger_status = f"网络闲置：{elapsed}/{self._network_idle_seconds} 秒"
            if self._network_idle_elapsed >= self._network_idle_seconds:
                self._network_timer.stop()
                self._network_trigger_active = False
                self._network_trigger_status = "网络闲置触发"
                self._add_log("网络闲置触发：达到设定闲置时长")
                self.networkTriggerChanged.emit()
                self._execute_with_script("网络闲置触发")
                return
        else:
            self._network_idle_elapsed = 0.0
            self._network_trigger_status = f"网络忙碌：0/{self._network_idle_seconds} 秒"
        self.networkTriggerChanged.emit()

    def _diagnostic_text(self):
        return "\n".join([
            "AutoShutdownQt 2.0 Diagnostics",
            f"Dry-run: {self._dry_run}",
            f"Status: {self._status}",
            f"Remaining seconds: {self._remaining_seconds}",
            f"Target info: {self._target_time_str or '(none)'}",
            f"Action: {self._selected_action} ({self.actionLabel})",
            f"Force close: {self._force_close}",
            f"Script enabled: {self._script_enabled}",
            f"Script path: {self._script_path or '(empty)'}",
            f"Script timeout seconds: {self._script_timeout_seconds}",
            f"Process trigger: active={self._process_trigger_active}, name={self._process_name or '(empty)'}, target={self._process_target_name or '(none)'}, status={self._process_trigger_status}",
            f"Network trigger: active={self._network_trigger_active}, down<{self._network_download_threshold_kbps} KB/s, up<{self._network_upload_threshold_kbps} KB/s, idle={self._network_idle_seconds}s, poll={self._network_poll_seconds}s, status={self._network_trigger_status}, speed={self._network_speed_text}",
        ])

    def _execute_power_action(self):
        if self._power_executor is not None:
            self._power_executor(self._selected_action, self._force_close)
            return
        from power_service import execute_power_action
        execute_power_action(self._selected_action, self._force_close)

    def _check_process_running(self, process_name):
        self._last_process_check_error = ""
        try:
            return bool(self._process_checker(process_name))
        except Exception as exc:
            self._last_process_check_error = str(exc) or exc.__class__.__name__
            return False

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
        except Exception as exc:
            self._last_process_check_error = str(exc) or exc.__class__.__name__
            return False
        if completed.returncode != 0:
            message = (completed.stderr or completed.stdout or f"tasklist exited with {completed.returncode}").strip()
            self._last_process_check_error = message
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

    def _settings_snapshot(self):
        return {
            "dryRun": self._dry_run,
            "forceClose": self._force_close,
            "selectedAction": self._selected_action,
            "scriptEnabled": self._script_enabled,
            "scriptPath": self._script_path,
            "scriptTimeoutSeconds": self._script_timeout_seconds,
            "processName": self._process_name,
            "processPollSeconds": self._process_poll_seconds,
            "networkDownloadThresholdKbps": self._network_download_threshold_kbps,
            "networkUploadThresholdKbps": self._network_upload_threshold_kbps,
            "networkIdleSeconds": self._network_idle_seconds,
            "networkPollSeconds": self._network_poll_seconds,
            "taskQueue": self._scheduler.to_settings(),
        }

    def _save_settings(self):
        if not self._persist_settings:
            return
        try:
            save_settings(self._settings_snapshot(), self._settings_path)
        except Exception as exc:
            self._add_log(f"设置保存失败：{exc}")

    def _should_persist_settings(self, settings_path):
        if settings_path is not None:
            return True
        app = QCoreApplication.instance()
        return bool(app and QCoreApplication.applicationName() == "AutoShutdownQt")

    def _now(self):
        return datetime.now()

    def _coerce_bool(self, value, fallback):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off"}:
                return False
        return fallback

    def _coerce_int(self, value, fallback, minimum=None):
        try:
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError("non-finite integer setting")
            coerced = int(value)
        except (TypeError, ValueError, OverflowError):
            coerced = fallback
        if minimum is not None:
            coerced = max(minimum, coerced)
        return coerced

    def _coerce_float(self, value, fallback, minimum=None):
        try:
            coerced = float(value)
            if not math.isfinite(coerced):
                raise ValueError("non-finite float setting")
        except (TypeError, ValueError, OverflowError):
            coerced = fallback
        if minimum is not None:
            coerced = max(minimum, coerced)
        return coerced

    def _coerce_action(self, value, fallback):
        return value if value in self.POWER_ACTIONS else fallback

    def _open_path(self, folder):
        if hasattr(os, "startfile"):
            os.startfile(str(folder))
            return
        if sys.platform == "darwin":
            subprocess.Popen(["open", str(folder)])
        else:
            subprocess.Popen(["xdg-open", str(folder)])
