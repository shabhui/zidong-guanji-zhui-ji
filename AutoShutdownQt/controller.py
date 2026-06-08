from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer, QCoreApplication, QThread
from PySide6.QtWidgets import QFileDialog
from datetime import datetime, timedelta
from pathlib import Path
import json
import math
import os
import subprocess
import sys
import threading

from history_service import HistoryEvent, append_history_event, clear_history, export_history_json, history_rows_json
from idle_service import WindowsIdleReader, format_idle_status
from network_service import NetworkReader, compute_speed
from music_service import NullMusicService
from execution_reporting import exception_text
from power_action_context import PowerActionContext
from script_service import run_script
from settings_service import default_settings, load_settings, log_export_path as default_log_export_path, save_settings
from task_model import RepeatRule, TaskTriggerType
from task_scheduler import TaskScheduler


TASK_SOURCE_LABELS = {
    "countdown": "手动倒计时",
    "clock": "指定时间",
    "template": "模板任务",
    "process": "进程退出触发",
    "network": "网络闲置触发",
    "idle": "空闲触发",
    "queue": "队列任务",
    "reminder": "执行前提醒",
    "active-countdown": "手动倒计时",
}


class AppController(QObject):
    remainingTimeChanged = Signal()
    statusChanged = Signal()
    targetInfoChanged = Signal()
    dryRunChanged = Signal()
    forceCloseChanged = Signal()
    closeAppsChanged = Signal()
    scriptConfigChanged = Signal()
    processTriggerChanged = Signal()
    networkTriggerChanged = Signal()
    idleTriggerChanged = Signal()
    logTextChanged = Signal()
    taskQueueChanged = Signal()
    schedulingPausedChanged = Signal()
    musicChanged = Signal()
    reminderChanged = Signal()
    historyChanged = Signal()
    startupChanged = Signal()
    powerActionProgressChanged = Signal()
    _workerLogRequested = Signal(str)
    _workerCallbackRequested = Signal(object)

    POWER_ACTIONS = ["shutdown", "sleep", "hibernate", "restart", "logoff", "lock"]
    CLOSE_APPS_MAX_TIMEOUT_SECONDS = 300
    ACTION_LABELS = {
        "shutdown": "关机", "sleep": "睡眠", "hibernate": "休眠",
        "restart": "重启", "logoff": "注销", "lock": "锁定",
    }
    STATUS_LABELS = {
        "ready": "就绪",
        "running": "运行中",
        "paused": "已暂停",
    }
    LOG_FILTER_LABELS = {
        "all": "全部",
        "info": "信息",
        "warning": "警告",
        "error": "错误",
    }

    def __init__(self, parent=None, settings_path=None, network_reader=None, idle_reader=None, log_export_path=None, open_folder=None, music_service=None, folder_picker=None, notification_service=None, startup_service=None, clipboard_writer=None):
        super().__init__(parent)
        self._workerLogRequested.connect(self._add_log)
        self._workerCallbackRequested.connect(self._run_worker_callback)
        self._power_action_lock = threading.Lock()
        self._power_action_in_progress = False
        self._power_action_progress_text = ""
        self._close_apps_skip_event = None
        self._close_apps_last_preview = "未运行"
        self._close_apps_last_result = "未运行"
        self._last_copied_text = ""
        self._copy_status_text = ""
        self._clipboard_writer = clipboard_writer
        self._log_filter = "all"
        self._health_check_text = "健康检查：尚未运行"
        self._settings_path = settings_path
        self._persist_settings = self._should_persist_settings(settings_path)
        settings = load_settings(settings_path) if self._persist_settings else default_settings()

        self._dry_run = self._coerce_bool(settings.get("dryRun"), True)
        self._selected_action = self._coerce_action(settings.get("selectedAction"), "shutdown")
        self._status = "ready"
        self._remaining_seconds = 0
        self._target_time_str = ""
        self._force_close = self._coerce_bool(settings.get("forceClose"), False)
        self._close_apps_before_action = self._coerce_bool(settings.get("closeAppsBeforeAction"), False)
        self._close_apps_timeout_seconds = self._coerce_close_apps_timeout(settings.get("closeAppsTimeoutSeconds"))
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
        self._idle_trigger_enabled = self._coerce_bool(settings.get("idleTriggerEnabled"), False)
        self._idle_minutes = self._coerce_int(settings.get("idleMinutes"), 30, minimum=1)
        self._idle_poll_seconds = self._coerce_int(settings.get("idlePollSeconds"), 10, minimum=1)
        self._idle_action = self._coerce_action(settings.get("idleAction"), "shutdown")
        self._music_autoplay_enabled = self._coerce_bool(settings.get("musicAutoplayEnabled"), True)
        self._music_volume = self._coerce_int(settings.get("musicVolume"), 70, minimum=0)
        self._music_volume = min(100, self._music_volume)
        self._music_folder = str(settings.get("musicFolder") or "")
        self._music_current_index = self._coerce_int(settings.get("musicCurrentIndex"), 0, minimum=0)
        self._music_playback_mode = self._coerce_music_playback_mode(settings.get("musicPlaybackMode"))
        self._reminder_enabled = self._coerce_bool(settings.get("reminderEnabled"), True)
        self._reminder_minutes_csv = str(settings.get("reminderMinutesCsv") or "10,5,1")
        self._snooze_minutes_value = self._coerce_int(settings.get("snoozeMinutes"), 15, minimum=1)
        self._history_settings = settings
        self._history_limit = self._coerce_int(settings.get("taskHistoryLimit"), 500, minimum=1)
        self._windows_notifications_enabled = self._coerce_bool(settings.get("windowsNotificationsEnabled"), True)
        self._start_with_windows = self._coerce_bool(settings.get("startWithWindows"), False)
        self._start_minimized_to_tray = self._coerce_bool(settings.get("startMinimizedToTray"), False)
        self._first_run_safety_guide_shown = self._coerce_bool(settings.get("firstRunSafetyGuideShown"), False)
        self._tray_close_hint_shown = self._coerce_bool(settings.get("trayCloseHintShown"), False)
        self._notification_service = notification_service
        self._startup_service = startup_service
        if self._startup_service is not None and hasattr(self._startup_service, "is_enabled"):
            self._start_with_windows = self._startup_service.is_enabled()
        self._shown_reminders = set()
        self._queue_reminder_task_id = ""
        self._reminder_dialog_title = ""
        self._reminder_dialog_body = ""
        self._reminder_dialog_snooze_text = ""
        self._network_trigger_active = False
        self._network_trigger_status = "未启动"
        self._network_speed_text = "等待网络监控"
        self._network_previous_sample = None
        self._network_idle_elapsed = 0.0
        self._idle_trigger_active = False
        self._idle_trigger_status = "未启动"
        self._idle_reader = idle_reader or WindowsIdleReader()
        self._logs = ["就绪 · 安全验证已开启" if self._dry_run else "就绪 · 真实执行模式"]
        self._script_runner = run_script
        self._power_executor = None
        self._app_closer = None
        self._process_checker = self._is_process_running
        self._last_process_check_error = ""
        self._network_reader = network_reader or NetworkReader()
        self._music_service = music_service or NullMusicService()
        if self._music_folder:
            self._music_service.set_folder(self._music_folder, self._music_current_index)
        self._music_service.playback_mode = self._music_playback_mode
        self._music_service.set_volume(self._music_volume)
        if hasattr(self._music_service, "playbackChanged"):
            self._music_service.playbackChanged.connect(self.musicChanged.emit)
        self._scheduler = TaskScheduler(now_provider=self._now, diagnostic_logger=self._add_log)
        self._scheduler.load_from_settings(settings.get("taskQueue"))
        self._log_export_path = log_export_path
        self._open_folder = open_folder
        self._folder_picker = folder_picker or self._pick_music_folder
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)
        if any(task.next_run_at for task in self._scheduler.tasks):
            self._timer.start()
        self._process_timer = QTimer(self)
        self._process_timer.timeout.connect(self._poll_process_trigger)
        self._network_timer = QTimer(self)
        self._network_timer.timeout.connect(self._poll_network_trigger)
        self._idle_timer = QTimer(self)
        self._idle_timer.timeout.connect(self._poll_idle_trigger)
        self._tray_service = None

    @staticmethod
    def _on_off(value):
        return "开启" if bool(value) else "关闭"

    @staticmethod
    def _yes_no(value):
        return "是" if bool(value) else "否"

    @staticmethod
    def _availability_label(value):
        return "可用" if bool(value) else "不可用"

    @classmethod
    def _status_label(cls, status):
        return cls.STATUS_LABELS.get(str(status), str(status))

    def _status_with_key(self):
        return f"{self._status_label(self._status)} ({self._status})"

    @staticmethod
    def _trigger_state_label(active, enabled=False):
        if active:
            return "监控中"
        if enabled:
            return "已启用"
        return "空闲"

    @staticmethod
    def _network_error_text(message):
        text = str(message or "").strip()
        labels = {
            "network unavailable": "网络不可用",
            "network counter reset": "网络计数已重置",
            "network counters unavailable": "无法读取网络计数",
            "netstat failed": "网络计数命令未成功",
        }
        return labels.get(text.lower(), text or "网络不可用")

    # --- QML Properties ---

    def getDryRun(self): return self._dry_run
    def setDryRun(self, v):
        v = bool(v)
        if self._dry_run != v:
            self._dry_run = v
            self._add_log("安全验证已开启" if v else "真实执行模式已开启")
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
        if self.powerActionInProgress:
            self._add_log("电源动作执行中，暂不能修改执行动作")
            return
        if v in self.POWER_ACTIONS and self._selected_action != v:
            self._selected_action = v
            self._add_log(f"已选择动作：{self.ACTION_LABELS.get(v, v)}")
            self._save_settings()
            self.targetInfoChanged.emit()
    selectedAction = Property(str, getSelectedAction, setSelectedAction, notify=targetInfoChanged)

    def getForceClose(self): return self._force_close
    def setForceClose(self, v):
        if self.powerActionInProgress:
            self._add_log("电源动作执行中，暂不能修改强制关闭设置")
            return
        v = bool(v)
        if self._force_close != v:
            self._force_close = v
            self._add_log("强制关闭已开启" if v else "强制关闭已关闭")
            self._save_settings()
            self.forceCloseChanged.emit()
    forceClose = Property(bool, getForceClose, setForceClose, notify=forceCloseChanged)

    def getCloseAppsBeforeAction(self): return self._close_apps_before_action
    def setCloseAppsBeforeAction(self, v):
        if self.powerActionInProgress:
            self._add_log("电源动作执行中，暂不能修改关机前优雅关闭应用设置")
            return
        v = bool(v)
        if self._close_apps_before_action != v:
            self._close_apps_before_action = v
            self._add_log("关机前优雅关闭应用已开启" if v else "关机前优雅关闭应用已关闭")
            self._save_settings()
            self.closeAppsChanged.emit()
    closeAppsBeforeAction = Property(bool, getCloseAppsBeforeAction, setCloseAppsBeforeAction, notify=closeAppsChanged)

    def getCloseAppsTimeoutSeconds(self): return self._close_apps_timeout_seconds
    def setCloseAppsTimeoutSeconds(self, v):
        if self.powerActionInProgress:
            self._add_log("电源动作执行中，暂不能修改关机前优雅关闭应用等待超时")
            return
        requested = self._coerce_int(v, 20, minimum=1)
        v = self._coerce_close_apps_timeout(v)
        if self._close_apps_timeout_seconds != v:
            self._close_apps_timeout_seconds = v
            if requested != v:
                self._add_log(f"关机前优雅关闭应用等待超时已调整为 {v} 秒")
            self._save_settings()
            self.closeAppsChanged.emit()
    closeAppsTimeoutSeconds = Property(int, getCloseAppsTimeoutSeconds, setCloseAppsTimeoutSeconds, notify=closeAppsChanged)

    def getPowerActionInProgress(self):
        with self._power_action_lock:
            return self._power_action_in_progress
    powerActionInProgress = Property(bool, getPowerActionInProgress, notify=powerActionProgressChanged)

    def getPowerActionProgressText(self):
        with self._power_action_lock:
            return self._power_action_progress_text
    powerActionProgressText = Property(str, getPowerActionProgressText, notify=powerActionProgressChanged)

    def getPowerActionStepSummaryText(self):
        with self._power_action_lock:
            in_progress = self._power_action_in_progress
            progress_text = self._power_action_progress_text
            can_skip = self._close_apps_skip_event is not None
        if not in_progress:
            return "就绪 | 脚本预检：等待 | 关闭应用：等待 | 系统动作：等待"
        parts = [
            "运行中",
            f"当前：{progress_text or '准备执行系统动作'}",
            "关闭应用：可跳过等待" if can_skip else "关闭应用：等待中",
        ]
        return " | ".join(parts)
    powerActionStepSummaryText = Property(str, getPowerActionStepSummaryText, notify=powerActionProgressChanged)

    def getCanSkipCloseAppsWait(self):
        with self._power_action_lock:
            return self._close_apps_skip_event is not None
    canSkipCloseAppsWait = Property(bool, getCanSkipCloseAppsWait, notify=powerActionProgressChanged)

    def getCloseAppsPreviewText(self): return self._close_apps_last_preview
    closeAppsPreviewText = Property(str, getCloseAppsPreviewText, notify=closeAppsChanged)

    def getCloseAppsLastResultText(self): return self._close_apps_last_result
    closeAppsLastResultText = Property(str, getCloseAppsLastResultText, notify=closeAppsChanged)

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

    def getIdleTriggerEnabled(self): return self._idle_trigger_enabled
    def setIdleTriggerEnabled(self, v):
        v = bool(v)
        if self._idle_trigger_enabled != v:
            self._idle_trigger_enabled = v
            self._save_settings()
            self.idleTriggerChanged.emit()
    idleTriggerEnabled = Property(bool, getIdleTriggerEnabled, setIdleTriggerEnabled, notify=idleTriggerChanged)

    def getIdleMinutes(self): return self._idle_minutes
    def setIdleMinutes(self, v):
        v = self._coerce_int(v, 30, minimum=1)
        if self._idle_minutes != v:
            self._idle_minutes = v
            self._save_settings()
            self.idleTriggerChanged.emit()
    idleMinutes = Property(int, getIdleMinutes, setIdleMinutes, notify=idleTriggerChanged)

    def getIdlePollSeconds(self): return self._idle_poll_seconds
    def setIdlePollSeconds(self, v):
        v = self._coerce_int(v, 10, minimum=1)
        if self._idle_poll_seconds != v:
            self._idle_poll_seconds = v
            if self._idle_trigger_active:
                self._idle_timer.setInterval(v * 1000)
            self._save_settings()
            self.idleTriggerChanged.emit()
    idlePollSeconds = Property(int, getIdlePollSeconds, setIdlePollSeconds, notify=idleTriggerChanged)

    def getIdleAction(self): return self._idle_action
    def setIdleAction(self, v):
        v = self._coerce_action(v, "shutdown")
        if self._idle_action != v:
            self._idle_action = v
            self._save_settings()
            self.idleTriggerChanged.emit()
    idleAction = Property(str, getIdleAction, setIdleAction, notify=idleTriggerChanged)

    def getIdleTriggerActive(self): return self._idle_trigger_active
    idleTriggerActive = Property(bool, getIdleTriggerActive, notify=idleTriggerChanged)

    def getIdleTriggerStatus(self): return self._idle_trigger_status
    idleTriggerStatus = Property(str, getIdleTriggerStatus, notify=idleTriggerChanged)

    def getMusicAutoplayEnabled(self): return self._music_autoplay_enabled
    def setMusicAutoplayEnabled(self, v):
        v = bool(v)
        if self._music_autoplay_enabled != v:
            self._music_autoplay_enabled = v
            self._add_log("启动自动播放音乐已开启" if v else "启动自动播放音乐已关闭")
            self._save_settings()
            self.musicChanged.emit()
    musicAutoplayEnabled = Property(bool, getMusicAutoplayEnabled, setMusicAutoplayEnabled, notify=musicChanged)

    def getMusicAvailable(self): return bool(self._music_service.available)
    musicAvailable = Property(bool, getMusicAvailable, notify=musicChanged)

    def getMusicTitle(self): return self._music_service.title
    musicTitle = Property(str, getMusicTitle, notify=musicChanged)

    def getMusicPlaying(self): return bool(self._music_service.playing)
    musicPlaying = Property(bool, getMusicPlaying, notify=musicChanged)

    def getMusicVolume(self): return self._music_volume
    musicVolume = Property(int, getMusicVolume, notify=musicChanged)

    def getMusicFolder(self): return str(getattr(self._music_service, "folder", self._music_folder))
    musicFolder = Property(str, getMusicFolder, notify=musicChanged)

    def getMusicCurrentIndex(self): return int(getattr(self._music_service, "current_index", self._music_current_index))
    musicCurrentIndex = Property(int, getMusicCurrentIndex, notify=musicChanged)

    def getMusicPositionMs(self): return int(getattr(self._music_service, "position_ms", 0))
    musicPositionMs = Property(int, getMusicPositionMs, notify=musicChanged)

    def getMusicDurationMs(self): return int(getattr(self._music_service, "duration_ms", 0))
    musicDurationMs = Property(int, getMusicDurationMs, notify=musicChanged)

    def getMusicPositionText(self): return str(getattr(self._music_service, "position_text", "00:00"))
    musicPositionText = Property(str, getMusicPositionText, notify=musicChanged)

    def getMusicDurationText(self): return str(getattr(self._music_service, "duration_text", "00:00"))
    musicDurationText = Property(str, getMusicDurationText, notify=musicChanged)

    def getMusicTracksJson(self):
        return json.dumps([
            {"index": index, "title": Path(track).name, "path": str(track)}
            for index, track in enumerate(getattr(self._music_service, "tracks", []))
        ], ensure_ascii=False)
    musicTracksJson = Property(str, getMusicTracksJson, notify=musicChanged)

    def getMusicPlaybackMode(self): return str(getattr(self._music_service, "playback_mode", self._music_playback_mode))
    musicPlaybackMode = Property(str, getMusicPlaybackMode, notify=musicChanged)

    def getReminderEnabled(self): return self._reminder_enabled
    def setReminderEnabled(self, v):
        v = bool(v)
        if self._reminder_enabled != v:
            self._reminder_enabled = v
            self._save_settings()
            self.reminderChanged.emit()
    reminderEnabled = Property(bool, getReminderEnabled, setReminderEnabled, notify=reminderChanged)

    def getReminderMinutesCsv(self): return self._reminder_minutes_csv
    def setReminderMinutesCsv(self, v):
        v = str(v or "")
        if self._reminder_minutes_csv != v:
            self._reminder_minutes_csv = v
            self._save_settings()
            self.reminderChanged.emit()
    reminderMinutesCsv = Property(str, getReminderMinutesCsv, setReminderMinutesCsv, notify=reminderChanged)

    def getSnoozeMinutesValue(self): return self._snooze_minutes_value
    def setSnoozeMinutesValue(self, v):
        v = self._coerce_int(v, 15, minimum=None)
        if v < 1:
            v = 15
        if self._snooze_minutes_value != v:
            self._snooze_minutes_value = v
            self._save_settings()
            self.reminderChanged.emit()
    snoozeMinutesValue = Property(int, getSnoozeMinutesValue, setSnoozeMinutesValue, notify=reminderChanged)

    def getHistoryRowsJson(self):
        return history_rows_json(self._history_settings)
    historyRowsJson = Property(str, getHistoryRowsJson, notify=historyChanged)

    def getTaskHistoryLimit(self): return self._history_limit
    def setTaskHistoryLimit(self, v):
        v = self._coerce_int(v, 500, minimum=1)
        if self._history_limit != v:
            self._history_limit = v
            self._history_settings["taskHistoryLimit"] = v
            self._trim_history_to_limit()
            self._save_settings()
            self.historyChanged.emit()
    taskHistoryLimit = Property(int, getTaskHistoryLimit, setTaskHistoryLimit, notify=historyChanged)

    def getWindowsNotificationsEnabled(self): return self._windows_notifications_enabled
    def setWindowsNotificationsEnabled(self, v):
        v = bool(v)
        if self._windows_notifications_enabled != v:
            self._windows_notifications_enabled = v
            self._save_settings()
            self.reminderChanged.emit()
    windowsNotificationsEnabled = Property(bool, getWindowsNotificationsEnabled, setWindowsNotificationsEnabled, notify=reminderChanged)

    def getStartWithWindows(self): return self._start_with_windows
    def setStartWithWindows(self, v):
        v = bool(v)
        if self._start_with_windows == v:
            return
        if self._startup_service is not None and not self._startup_service.set_enabled(v):
            self._add_log("开机启动设置失败")
            return
        self._start_with_windows = v
        self._save_settings()
        self.startupChanged.emit()
    startWithWindows = Property(bool, getStartWithWindows, setStartWithWindows, notify=startupChanged)

    def getStartMinimizedToTray(self): return self._start_minimized_to_tray
    def setStartMinimizedToTray(self, v):
        v = bool(v)
        if self._start_minimized_to_tray != v:
            self._start_minimized_to_tray = v
            self._save_settings()
            self.startupChanged.emit()
    startMinimizedToTray = Property(bool, getStartMinimizedToTray, setStartMinimizedToTray, notify=startupChanged)

    def getFirstRunSafetyGuideShown(self): return self._first_run_safety_guide_shown
    @Slot()
    def acknowledgeFirstRunSafetyGuide(self):
        if not self._first_run_safety_guide_shown:
            self._first_run_safety_guide_shown = True
            self._save_settings()
            self.startupChanged.emit()
    firstRunSafetyGuideShown = Property(bool, getFirstRunSafetyGuideShown, notify=startupChanged)

    def getTrayCloseHintShown(self): return self._tray_close_hint_shown
    @Slot()
    def acknowledgeTrayCloseHint(self):
        if not self._tray_close_hint_shown:
            self._tray_close_hint_shown = True
            self._save_settings()
            self.startupChanged.emit()
    trayCloseHintShown = Property(bool, getTrayCloseHintShown, notify=startupChanged)

    def getReminderDialogTitle(self): return self._reminder_dialog_title
    reminderDialogTitle = Property(str, getReminderDialogTitle, notify=reminderChanged)


    def getReminderDialogBody(self): return self._reminder_dialog_body
    reminderDialogBody = Property(str, getReminderDialogBody, notify=reminderChanged)

    def getReminderDialogSnoozeText(self): return self._reminder_dialog_snooze_text
    reminderDialogSnoozeText = Property(str, getReminderDialogSnoozeText, notify=reminderChanged)

    def getLogText(self): return "\n".join(self._logs[-8:])
    logText = Property(str, getLogText, notify=logTextChanged)

    def getFilteredLogText(self):
        rows = self._filtered_logs()
        return "\n".join(rows[-8:])
    filteredLogText = Property(str, getFilteredLogText, notify=logTextChanged)

    def getLogFilter(self):
        return self._log_filter
    logFilter = Property(str, getLogFilter, notify=logTextChanged)

    def getLogSummaryText(self):
        total = len(self._logs)
        latest = self._logs[-1] if self._logs else "(none)"
        failures = [
            entry for entry in self._logs
            if any(marker in entry for marker in ("失败", "错误", "不可用", "failed", "error"))
        ]
        if failures:
            return f"日志：共 {total} 条 · 最近失败：{self._strip_log_timestamp(failures[-1])}"
        return f"日志：共 {total} 条 · 最近：{self._strip_log_timestamp(latest)}"
    logSummaryText = Property(str, getLogSummaryText, notify=logTextChanged)

    def getLogCategorySummaryText(self):
        counts = {"info": 0, "warning": 0, "error": 0}
        for entry in self._logs:
            lower = str(entry).lower()
            if any(marker in lower for marker in ("warning", "warn", "danger", "警告")):
                counts["warning"] += 1
            elif any(marker in lower for marker in ("failed", "error", "失败", "错误", "不可用", "拒绝")):
                counts["error"] += 1
            else:
                counts["info"] += 1
        return f"日志分类：信息={counts['info']} 警告={counts['warning']} 错误={counts['error']}"
    logCategorySummaryText = Property(str, getLogCategorySummaryText, notify=logTextChanged)

    def getDiagnosticText(self):
        return self._diagnostic_text()
    diagnosticText = Property(str, getDiagnosticText, notify=logTextChanged)

    def getLastCopiedText(self):
        return self._last_copied_text
    lastCopiedText = Property(str, getLastCopiedText, notify=logTextChanged)

    def getCopyStatusText(self):
        return self._copy_status_text
    copyStatusText = Property(str, getCopyStatusText, notify=logTextChanged)

    def getHealthCheckText(self):
        return self._health_check_text
    healthCheckText = Property(str, getHealthCheckText, notify=logTextChanged)

    def getQueueTaskCount(self):
        return len(self._scheduler.tasks)
    queueTaskCount = Property(int, getQueueTaskCount, notify=taskQueueChanged)

    def getQueueText(self):
        rows = self._scheduler.rows()
        if not rows:
            return "暂无任务"
        return "\n".join(
            f"{row['name']} · {row['triggerSummary']} · {row['repeatSummary']} · {row.get('statusLabel') or row['status']} · {row['nextRunText']}"
            + (f" · {row['lastError']}" if row.get("lastError") else "")
            for row in rows
        )
    queueText = Property(str, getQueueText, notify=taskQueueChanged)

    def getQueueSummaryText(self):
        rows = self._scheduler.rows()
        if not rows:
            return "队列摘要：暂无任务"
        labels = {
            "pending": "待执行",
            "active": "监控中",
            "paused": "暂停",
            "completed": "完成",
            "failed": "失败",
            "unknown": "未知状态",
        }
        counts = {}
        for row in rows:
            status = str(row.get("status") or "unknown")
            status_key = status if status in labels else "unknown"
            counts[status_key] = counts.get(status_key, 0) + 1
        parts = [
            f"{labels.get(status, '未知状态')} {count}"
            for status, count in counts.items()
            if count
        ]
        failed_errors = [
            str(row.get("lastError") or "")
            for row in rows
            if row.get("status") == "failed" and row.get("lastError")
        ]
        suffix = f" · 最近失败：{failed_errors[-1]}" if failed_errors else ""
        return "队列摘要：" + "，".join(parts) + suffix
    queueSummaryText = Property(str, getQueueSummaryText, notify=taskQueueChanged)

    def getQueueRowsJson(self):
        return json.dumps(self._scheduler.rows(), ensure_ascii=False)
    queueRowsJson = Property(str, getQueueRowsJson, notify=taskQueueChanged)

    def getSafetySummaryText(self):
        mode = "安全验证" if self._dry_run else "真实执行"
        script = self._on_off(self._script_enabled)
        close_apps = self._on_off(self._close_apps_before_action)
        force_close = self._on_off(self._force_close)
        return (
            f"安全摘要：模式={mode} 动作={self._selected_action}（{self.actionLabel}） "
            f"脚本={script} 关机前关闭应用={close_apps} 强制关闭={force_close}"
        )
    safetySummaryText = Property(str, getSafetySummaryText, notify=targetInfoChanged)

    def getTriggerHealthSummaryText(self):
        process_state = self._trigger_state_label(self._process_trigger_active)
        network_state = self._trigger_state_label(self._network_trigger_active)
        idle_state = self._trigger_state_label(self._idle_trigger_active, self._idle_trigger_enabled)
        return (
            f"触发器状态：进程={process_state}（{self._process_trigger_status}）；"
            f"网络={network_state}（{self._network_trigger_status}）；"
            f"空闲={idle_state}（{self._idle_trigger_status}）"
        )
    triggerHealthSummaryText = Property(str, getTriggerHealthSummaryText, notify=processTriggerChanged)

    def getSchedulingPaused(self):
        return self._scheduler.paused
    schedulingPaused = Property(bool, getSchedulingPaused, notify=schedulingPausedChanged)

    def getTrayService(self):
        return self._tray_service

    def setTrayService(self, service):
        self._tray_service = service
        self.startupChanged.emit()
    trayService = property(getTrayService, setTrayService)

    def getTrayAvailable(self):
        return bool(self._tray_service is not None and getattr(self._tray_service, "available", False))
    trayAvailable = Property(bool, getTrayAvailable, notify=startupChanged)

    @Slot(str, result=str)
    def taskSourceLabel(self, source):
        return TASK_SOURCE_LABELS.get(str(source or ""), "未知来源")

    @Slot(result=bool)
    def minimizeToTray(self):
        if self._tray_service is None:
            self._add_log("最小化到托盘已跳过：托盘不可用")
            return False
        minimized = self._tray_service.minimize_to_tray()
        if not minimized:
            self._add_log("最小化到托盘已跳过：托盘不可用")
        return minimized

    def getNotificationService(self):
        return self._notification_service

    def setNotificationService(self, service):
        self._notification_service = service
    notificationService = property(getNotificationService, setNotificationService)

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
        self._record_history("created", task.action, task.trigger_type.value, task.id, f"已加入任务队列：{task.name}")
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
        self._record_history("created", task.action, task.trigger_type.value, task.id, f"已加入任务队列：{task.name}")
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
        force_text = "开启" if task.force_close else "关闭"
        self._add_log(f"安全检查：{task.name} -> {task.action}（强制关闭：{force_text}）")

    @Slot(str)
    def copyQueueTaskDiagnostic(self, task_id):
        try:
            task = self._scheduler.get_task(task_id)
        except KeyError:
            self._add_log(f"任务不存在：{task_id}")
            return
        payload = {
            "id": task.id,
            "name": task.name,
            "action": task.action,
            "actionLabel": self.ACTION_LABELS.get(task.action, task.action),
            "forceClose": task.force_close,
            "forceCloseLabel": "开启" if task.force_close else "关闭",
            "triggerType": task.trigger_type.value,
            "triggerSummary": task.trigger_summary(),
            "repeatRule": task.repeat_rule.value,
            "repeatSummary": task.repeat_summary(),
            "enabled": task.enabled,
            "status": task.status.value,
            "statusLabel": {
                "pending": "待执行",
                "active": "监控中",
                "paused": "已暂停",
                "completed": "已完成",
                "failed": "失败",
            }.get(task.status.value, "未知状态"),
            "nextRunAt": task.next_run_at.isoformat() if task.next_run_at else None,
            "lastRunAt": task.last_run_at.isoformat() if task.last_run_at else None,
            "lastError": task.last_error,
        }
        self._copy_text("=== 队列任务诊断 ===\n" + json.dumps(payload, ensure_ascii=False, indent=2))
        self._add_log(f"队列任务诊断已复制：{task.id}")

    @Slot(str)
    def retryQueueTask(self, task_id):
        try:
            task = self._scheduler.get_task(task_id)
        except KeyError:
            self._add_log(f"任务不存在：{task_id}")
            return
        if task.status.value != "failed":
            self._add_log(f"任务未失败，无法重试：{task.name}")
            return
        previous_action = self._selected_action
        previous_force_close = self._force_close
        self._selected_action = task.action
        self._force_close = task.force_close

        def mark_retry_executed(success, error):
            self._mark_queue_task_execution(
                task,
                self._now(),
                success,
                error,
                log_prefix="队列任务重试",
            )

        try:
            result = self._execute_with_script(
                f"重试队列任务：{task.name}",
                completion=mark_retry_executed,
                source="queue-retry",
                task_id=task.id,
            )
            if result is None:
                self._add_log(f"队列任务重试已开始：{task.name}")
                return
            success, error = result
            mark_retry_executed(success, error)
        finally:
            self._selected_action = previous_action
            self._force_close = previous_force_close

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
        if self.powerActionInProgress:
            self._add_log("电源动作执行中，暂不能切换安全验证")
            return
        self.dryRun = bool(enabled)
        if not self._dry_run:
            self._add_log("真实执行模式已开启：请确认动作、触发器、脚本路径和未保存工作")

    @Slot()
    def startMusicAutoplay(self):
        if self._music_autoplay_enabled:
            self.playMusic()

    @Slot()
    def playMusic(self):
        if self._music_service.play():
            self._add_log(f"开始播放音乐：{self._music_service.title}")
        else:
            self._add_log("未找到音乐文件，无法播放")
        self.musicChanged.emit()

    @Slot()
    def pauseMusic(self):
        self._music_service.pause()
        self._add_log("音乐已暂停")
        self.musicChanged.emit()

    @Slot()
    def stopMusic(self):
        self._music_service.stop()
        self._add_log("音乐已停止")
        self.musicChanged.emit()

    @Slot(int)
    def setMusicVolume(self, value):
        value = self._coerce_int(value, 70, minimum=0)
        value = min(100, value)
        if self._music_volume != value:
            self._music_volume = value
            self._music_service.set_volume(value)
            self._save_settings()
            self.musicChanged.emit()

    @Slot(int)
    def playMusicTrack(self, index):
        if self._music_service.select_track(index, autoplay=True):
            self._music_current_index = int(getattr(self._music_service, "current_index", index))
            self._save_settings()
            self._add_log(f"开始播放音乐：{self._music_service.title}")
        else:
            self._add_log(f"音乐序号无效：{index}")
        self.musicChanged.emit()

    @Slot(int)
    def seekMusic(self, position_ms):
        self._music_service.seek(position_ms)
        self.musicChanged.emit()

    @Slot()
    def chooseMusicFolder(self):
        folder = self._folder_picker()
        if not folder:
            return
        self._music_folder = str(folder)
        self._music_current_index = 0
        self._music_service.set_folder(self._music_folder, self._music_current_index)
        self._save_settings()
        self._add_log(f"已选择音乐文件夹：{self._music_folder}")
        self.musicChanged.emit()

    @Slot()
    def nextMusicTrack(self):
        if self._music_service.next_track():
            self._music_current_index = int(getattr(self._music_service, "current_index", self._music_current_index))
            self._save_settings()
            self._add_log(f"下一首：{self._music_service.title}")
        else:
            self._add_log("没有可播放的下一首")
        self.musicChanged.emit()

    @Slot()
    def previousMusicTrack(self):
        if self._music_service.previous_track():
            self._music_current_index = int(getattr(self._music_service, "current_index", self._music_current_index))
            self._save_settings()
            self._add_log(f"上一首：{self._music_service.title}")
        else:
            self._add_log("没有可播放的上一首")
        self.musicChanged.emit()

    @Slot(str)
    def setMusicPlaybackMode(self, mode):
        mode = self._coerce_music_playback_mode(mode)
        self._music_playback_mode = mode
        self._music_service.playback_mode = mode
        self._save_settings()
        self.musicChanged.emit()

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
        self._shown_reminders.clear()
        self._add_log(f"已延后 {minutes} 分钟")
        self._record_history("snoozed", self._selected_action, "active-countdown", "", f"已延后 {minutes} 分钟")
        self.remainingTimeChanged.emit()
        self.targetInfoChanged.emit()

    @Slot()
    def snoozeCurrentTask(self):
        minutes = self._snooze_minutes_value
        if self._status == "running":
            self._remaining_seconds += minutes * 60
            self._target_time_str = ""
            self._shown_reminders.clear()
            self._add_log(f"已延后 {minutes} 分钟")
            self._record_history("snoozed", self._selected_action, "active-countdown", "", f"已延后 {minutes} 分钟")
            self.remainingTimeChanged.emit()
            self.targetInfoChanged.emit()
            self.reminderChanged.emit()
            return
        task = self._next_snoozable_task()
        if task is None:
            self._add_log("没有可延后的任务")
            return
        task.next_run_at = task.next_run_at + timedelta(minutes=minutes)
        if task.trigger_type == TaskTriggerType.COUNTDOWN:
            task.trigger_config["seconds"] = max(1, int(task.trigger_config.get("seconds", 0))) + minutes * 60
        self._shown_reminders.clear()
        self._save_settings()
        self._add_log(f"已延后 {minutes} 分钟")
        self._record_history("snoozed", task.action, task.trigger_type.value, task.id, f"已延后 {minutes} 分钟")
        self.taskQueueChanged.emit()
        self.reminderChanged.emit()

    def _next_snoozable_task(self):
        candidates = [task for task in self._scheduler.tasks if task.enabled and task.next_run_at]
        if not candidates:
            return None
        return sorted(candidates, key=lambda task: (task.next_run_at, task.created_order))[0]

    @Slot()
    def cancelCurrentTask(self):
        if self._queue_reminder_task_id:
            if self._scheduler.remove_task(self._queue_reminder_task_id):
                cancelled_task_id = self._queue_reminder_task_id
                self._queue_reminder_task_id = ""
                self._shown_reminders.clear()
                self._save_settings()
                self._add_log("已取消当前任务")
                self._record_history("cancelled", self._selected_action, "queue", cancelled_task_id, "已取消当前任务")
                self.taskQueueChanged.emit()
                self.reminderChanged.emit()
                return
        self.cancel()

    @Slot()
    def cancel(self):
        self._timer.stop()
        self._remaining_seconds = 0
        self._status = "ready"
        self._target_time_str = ""
        self._shown_reminders.clear()
        self._add_log("已取消当前任务")
        self._record_history("cancelled", self._selected_action, "active-countdown", "", "已取消当前任务")
        self.statusChanged.emit()
        self.remainingTimeChanged.emit()
        self.targetInfoChanged.emit()

    @Slot()
    def testScript(self):
        if not self._script_enabled:
            self._add_log("执行前脚本未启用")
            return
        if self._dry_run:
            self._add_log(f"安全验证：将执行脚本 {self._script_path or '(未设置路径)'}")
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
            message = self._network_error_text(sample.message)
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
    def startIdleTrigger(self):
        sample = self._idle_reader.sample()
        if not sample.available:
            self._idle_trigger_active = False
            self._idle_trigger_status = format_idle_status(None, self._idle_minutes * 60, sample.message)
            self._add_log(f"空闲触发未启动：{self._idle_trigger_status}")
            self.idleTriggerChanged.emit()
            return
        self._idle_trigger_enabled = True
        self._idle_trigger_active = True
        self._idle_trigger_status = format_idle_status(sample.idle_seconds, self._idle_minutes * 60)
        self._idle_timer.setInterval(self._idle_poll_seconds * 1000)
        self._idle_timer.start()
        if self._remove_queue_tasks_by_trigger(TaskTriggerType.IDLE):
            self._add_log("已替换上一空闲触发队列任务")
        self._save_settings()
        self._add_log("空闲触发已启动")
        self.taskQueueChanged.emit()
        self.idleTriggerChanged.emit()

    @Slot()
    def stopIdleTrigger(self):
        self._stop_idle_monitor_without_queue_update()
        removed_tasks = self._remove_queue_tasks_by_trigger(TaskTriggerType.IDLE)
        self._save_settings()
        self._add_log("空闲触发已停止")
        if removed_tasks:
            self.taskQueueChanged.emit()
        self.idleTriggerChanged.emit()

    @Slot()
    def clearLogs(self):
        self._logs = ["就绪 · 日志已清空"]
        self.logTextChanged.emit()

    @Slot()
    def exportLogs(self):
        target = Path(self._log_export_path) if self._log_export_path is not None else default_log_export_path()
        try:
            target = target.expanduser()
            target.parent.mkdir(parents=True, exist_ok=True)
            content = "=== 诊断信息 ===\n" + self._diagnostic_text() + "\n\n=== 最近日志 ===\n" + "\n".join(self._logs) + "\n"
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
    def copyDiagnostics(self):
        self._copy_text(self._diagnostic_text())
        self._add_log("诊断已复制")

    @Slot(str)
    def setLogFilter(self, value):
        value = str(value or "all").lower()
        self._log_filter = value if value in ("all", "info", "warning", "error") else "all"
        self._add_log(f"日志筛选：{self.LOG_FILTER_LABELS.get(self._log_filter, self._log_filter)}")

    @Slot()
    def runHealthCheck(self):
        script_state = "未启用"
        if self._script_enabled:
            script_state = "正常" if self._normalize_script_path_for_execution() else "无效"
        parts = [
            "健康检查",
            f"脚本={script_state}",
            f"关闭应用服务={self._availability_label(self._close_apps_service_available())}",
            f"队列={self.queueSummaryText}",
            f"触发器={self.triggerHealthSummaryText}",
            f"安全={self.safetySummaryText}",
        ]
        self._health_check_text = " | ".join(parts)
        self._add_log(self._health_check_text)

    @Slot()
    def clearHistory(self):
        clear_history(self._history_settings)
        self._save_settings()
        self.historyChanged.emit()
        self._add_log("历史记录已清空")

    @Slot()
    def exportHistory(self):
        log_target = Path(self._log_export_path) if self._log_export_path is not None else default_log_export_path()
        target = log_target.expanduser().with_name("AutoShutdownQt-history.json")
        try:
            export_history_json(self._history_settings, target)
        except Exception as exc:
            self._add_log(f"历史导出失败：{exc}")
            return
        self._add_log(f"历史已导出：{target}")

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

    @Slot()
    def skipCloseAppsWait(self):
        with self._power_action_lock:
            event = self._close_apps_skip_event
        if event is None:
            self._add_log("没有正在等待的优雅关闭应用流程")
            return
        event.set()
        self._add_log("已跳过优雅关闭等待，将继续执行电源动作")

    @Slot()
    def previewCloseApps(self):
        try:
            closer = self._get_app_closer()
            windows = list(closer.list_app_windows())
        except Exception as exc:
            self._close_apps_last_preview = f"失败：{exc}"
            self._add_log(f"关闭应用预检失败：{exc}")
            self.closeAppsChanged.emit()
            return
        if not windows:
            self._close_apps_last_preview = "没有需要关闭的应用"
            self._add_log("关闭应用预检：没有需要优雅关闭的应用")
            self.closeAppsChanged.emit()
            return
        names = self._summarize_titles(w.title for w in windows)
        self._close_apps_last_preview = f"{len(windows)} 个应用：{names}"
        self._add_log(f"关闭应用预检：将请求关闭 {len(windows)} 个应用：{names}")
        self.closeAppsChanged.emit()

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
        self._check_queue_execution_reminders(now)
        if self._remaining_seconds <= 0:
            return
        self._remaining_seconds -= 1
        self.remainingTimeChanged.emit()
        self._check_execution_reminders()
        if self._remaining_seconds <= 0:
            self._timer.stop()
            self._status = "ready"
            self._shown_reminders.clear()
            self.statusChanged.emit()
            self._execute_with_script("倒计时结束")

    def _check_execution_reminders(self):
        if not self._reminder_enabled or self._status != "running" or self._remaining_seconds <= 0:
            return
        for minute in self._reminder_minutes():
            threshold_seconds = minute * 60
            if self._remaining_seconds <= threshold_seconds and minute not in self._shown_reminders:
                self._shown_reminders.add(minute)
                self._show_execution_reminder(minute)
                return

    def _show_execution_reminder(self, minute):
        mode_text = "安全验证：到点只记录将要执行的动作，不会真实执行。" if self._dry_run else "真实执行：到点会执行系统动作，请确认未保存工作。"
        self._reminder_dialog_title = "执行前提醒"
        self._reminder_dialog_body = f"{self.actionLabel} 将在 {self.remainingText} 后执行。\n{mode_text}"
        self._reminder_dialog_snooze_text = f"延后 {self._snooze_minutes_value} 分钟"
        self._add_log(f"执行前提醒：剩余 {minute} 分钟")
        self._record_history("reminder", self._selected_action, "reminder", self._queue_reminder_task_id, f"执行前提醒：剩余 {minute} 分钟")
        if self._windows_notifications_enabled and self._notification_service is not None:
            self._notification_service.show_reminder(self._reminder_dialog_title, self._reminder_dialog_body)
        self.reminderChanged.emit()

    def _check_queue_execution_reminders(self, now):
        task = self._next_snoozable_task()
        if task is None or not task.next_run_at:
            return
        previous_action = self._selected_action
        previous_force_close = self._force_close
        previous_remaining = self._remaining_seconds
        previous_status = self._status
        if self._queue_reminder_task_id != task.id:
            self._queue_reminder_task_id = task.id
            self._shown_reminders.clear()
        self._selected_action = task.action
        self._force_close = task.force_close
        self._remaining_seconds = max(0, int((task.next_run_at - now).total_seconds()))
        self._status = "running"
        try:
            self._check_execution_reminders()
        finally:
            self._selected_action = previous_action
            self._force_close = previous_force_close
            self._remaining_seconds = previous_remaining
            self._status = previous_status

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

    def _stop_idle_monitor_without_queue_update(self):
        self._idle_timer.stop()
        self._idle_trigger_active = False
        self._idle_trigger_status = "已停止"

    def _mark_queue_task_execution(self, task, executed_at, success, error="", log_prefix=""):
        self._scheduler.mark_executed(task.id, executed_at, success=success, error=error)
        self._save_settings()
        self.taskQueueChanged.emit()
        if log_prefix:
            result_text = "已完成" if success else "失败"
            self._add_log(f"{log_prefix}{result_text}：{task.name}")

    def _execute_task(self, task, now):
        previous_action = self._selected_action
        previous_force_close = self._force_close
        self._selected_action = task.action
        self._force_close = task.force_close

        def mark_task_executed(success, error):
            self._mark_queue_task_execution(task, now, success, error)

        try:
            result = self._execute_with_script(
                f"任务队列触发：{task.name}",
                completion=mark_task_executed,
                source="queue",
                task_id=task.id,
            )
            if result is not None:
                success, error = result
                mark_task_executed(success, error)
        except Exception as exc:
            self._mark_queue_task_execution(task, now, False, exception_text(exc))
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

    def _power_action_context(self, reason, completion=None, source="", task_id=""):
        return PowerActionContext(
            reason=reason,
            action=self._selected_action,
            force_close=self._force_close,
            close_apps_timeout_seconds=self._close_apps_timeout_seconds,
            completion=completion,
            source=source,
            task_id=task_id,
        )

    def _execute_with_script(self, reason, completion=None, source="", task_id=""):
        context = self._power_action_context(reason, completion, source=source, task_id=task_id)
        if self._script_enabled:
            if self._dry_run:
                self._add_log(f"安全验证：将执行脚本 {self._script_path or '(未设置路径)'}")
            else:
                script_path = self._validate_script_before_real_execution()
                if not script_path:
                    return False, "脚本路径无效"
                result = self._script_runner(script_path, self._script_timeout_seconds)
                self._add_log(result.message)
                if not result.ok:
                    self._add_log("脚本失败，已阻止电源动作")
                    return False, result.message
        if self._dry_run:
            self._maybe_close_apps(context.action)
            force_text = "开启" if context.force_close else "关闭"
            message = f"安全验证：将执行 {context.action}（强制关闭：{force_text}）"
            self._add_log(message)
            self._record_history("dry-run", context.action, context.reason, "", message)
            return True, ""
        if not self._begin_power_action():
            error = "已有电源动作正在执行"
            self._add_log(f"{error}，已忽略重复触发")
            return False, error
        if self._should_close_apps_before_live_action(context.action):
            self._start_close_apps_then_power_action(
                context.reason,
                context.action,
                context.force_close,
                context.close_apps_timeout_seconds,
                context.completion,
            )
            return None
        try:
            return self._execute_live_power_action(context.reason, context.action, context.force_close)
        finally:
            self._finish_power_action()

    def _execute_live_power_action(self, reason, action, force_close):
        label = self.ACTION_LABELS.get(action, action)
        self._set_power_action_progress_text(f"正在执行 {label}")
        self._log_from_any_thread(f"{reason}：执行 {label}")
        try:
            result = self._execute_power_action_for(action, force_close)
            if result is False:
                error = "系统拒绝或命令返回失败"
                self._log_from_any_thread(f"电源动作执行失败：{error}")
                return False, error
        except Exception as exc:
            error = exception_text(exc)
            self._log_from_any_thread(f"电源动作执行失败：{error}")
            return False, error
        return True, ""

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
            message = self._network_error_text(speed.message or current.message)
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

    def _poll_idle_trigger(self):
        if not self._idle_trigger_active:
            return
        sample = self._idle_reader.sample()
        if not sample.available:
            self._idle_timer.stop()
            self._idle_trigger_active = False
            self._idle_trigger_status = format_idle_status(None, self._idle_minutes * 60, sample.message)
            self._add_log(f"空闲触发已停止：{self._idle_trigger_status}")
            self.idleTriggerChanged.emit()
            return

        threshold_seconds = self._idle_minutes * 60
        previous_status = self._idle_trigger_status
        self._idle_trigger_status = format_idle_status(sample.idle_seconds, threshold_seconds)
        changed = self._idle_trigger_status != previous_status
        if sample.idle_seconds >= threshold_seconds:
            self._idle_timer.stop()
            self._idle_trigger_active = False
            changed = True
            if self._remove_queue_tasks_by_trigger(TaskTriggerType.IDLE):
                self._add_log("已替换上一空闲触发队列任务")
            self._scheduler.add_task(
                "空闲触发",
                self._idle_action,
                self._force_close,
                TaskTriggerType.IDLE,
                {
                    "idleMinutes": self._idle_minutes,
                    "pollSeconds": self._idle_poll_seconds,
                },
                RepeatRule.ONCE,
            )
            self._save_settings()
            self._add_log("空闲触发：达到设定空闲时长，已加入任务队列")
            self.taskQueueChanged.emit()
        if changed:
            self.idleTriggerChanged.emit()

    def _diagnostic_text(self):
        return "\n".join([
            "定时关机助手 3.2 诊断信息",
            f"安全验证：{'开启' if self._dry_run else '关闭'}",
            f"状态：{self._status_with_key()}",
            f"剩余秒数：{self._remaining_seconds}",
            f"目标信息：{self._target_time_str or '无'}",
            f"动作：{self._selected_action}（{self.actionLabel}）",
            f"强制关闭：{self._on_off(self._force_close)}",
            f"关机前关闭应用：{self._on_off(self._close_apps_before_action)}（超时 {self._close_apps_timeout_seconds} 秒）",
            f"关闭应用服务：{self._availability_label(self._close_apps_service_available())}，已缓存={self._yes_no(self._app_closer is not None)}",
            f"关闭应用预览：{self._close_apps_last_preview}",
            f"最近关闭结果：{self._close_apps_last_result}",
            f"电源动作进行中：{self._yes_no(self.powerActionInProgress)}",
            f"电源动作进度：{self.powerActionProgressText or '无'}",
            self.safetySummaryText,
            self.triggerHealthSummaryText,
            f"队列摘要：{self.queueSummaryText}",
            f"日志摘要：{self.logSummaryText}",
            self.logCategorySummaryText,
            f"脚本启用：{self._yes_no(self._script_enabled)}",
            f"脚本路径：{self._script_path or '空'}",
            f"脚本超时秒数：{self._script_timeout_seconds}",
            f"进程触发器：监控={self._yes_no(self._process_trigger_active)}，进程={self._process_name or '空'}，目标={self._process_target_name or '无'}，状态={self._process_trigger_status}",
            f"网络触发器：监控={self._yes_no(self._network_trigger_active)}，下载<{self._network_download_threshold_kbps} KB/s，上传<{self._network_upload_threshold_kbps} KB/s，闲置={self._network_idle_seconds} 秒，轮询={self._network_poll_seconds} 秒，状态={self._network_trigger_status}，速度={self._network_speed_text}",
            f"空闲触发器：启用={self._yes_no(self._idle_trigger_enabled)}，监控={self._yes_no(self._idle_trigger_active)}，分钟={self._idle_minutes}，轮询={self._idle_poll_seconds} 秒，动作={self._idle_action}，状态={self._idle_trigger_status}",
        ])

    def _execute_power_action(self):
        return self._execute_power_action_for(self._selected_action, self._force_close)

    def _execute_power_action_for(self, action, force_close):
        if self._power_executor is not None:
            return self._power_executor(action, force_close)
        from power_service import execute_power_action
        return execute_power_action(action, force_close)

    def _close_apps_supported(self, action):
        # Only session-ending actions benefit from closing apps beforehand.
        return action in ("shutdown", "restart", "logoff")

    def _get_app_closer(self):
        if self._app_closer is None:
            from app_close_service import WindowsAppCloser
            self._app_closer = WindowsAppCloser()
        return self._app_closer

    def _close_apps_service_available(self):
        try:
            from app_close_service import WindowsAppCloser  # noqa: F401
            return True
        except Exception:
            return False

    def _should_close_apps_before_live_action(self, action=None):
        action = self._selected_action if action is None else action
        return (
            self._close_apps_before_action
            and not self._dry_run
            and self._close_apps_supported(action)
        )

    def _start_close_apps_then_power_action(self, reason, action, force_close, timeout_seconds, completion=None):
        label = self.ACTION_LABELS.get(action, action)
        self._set_power_action_progress_text(f"正在优雅关闭应用，完成后执行 {label}")
        skip_event = threading.Event()
        self._set_close_apps_skip_event(skip_event)
        try:
            closer = self._get_app_closer()
        except Exception as exc:
            self._add_log(f"优雅关闭应用不可用：{exc}")
            try:
                success, error = self._execute_live_power_action(reason, action, force_close)
            finally:
                self._set_close_apps_skip_event(None, expected=skip_event)
                self._finish_power_action()
            self._notify_power_action_complete(completion, success, error)
            return
        self._add_log(f"正在后台优雅关闭应用，完成后执行 {label}")
        worker = threading.Thread(
            target=self._close_apps_then_execute_power_action,
            args=(reason, action, force_close, closer, timeout_seconds, completion, skip_event),
            name="AutoShutdownQtCloseAppsPowerAction",
            daemon=False,
        )
        worker.start()

    def _close_apps_then_execute_power_action(self, reason, action, force_close, closer, timeout_seconds, completion, skip_event):
        success = False
        error = ""
        try:
            self._close_apps_with_closer(closer, timeout_seconds, should_stop=skip_event.is_set)
            self._set_close_apps_skip_event(None, expected=skip_event)
            success, error = self._execute_live_power_action(reason, action, force_close)
        finally:
            self._set_close_apps_skip_event(None, expected=skip_event)
            self._finish_power_action()
            self._notify_power_action_complete(completion, success, error)

    def _close_apps_with_closer(self, closer, timeout_seconds, should_stop=None):
        try:
            from app_close_service import close_user_apps
            result = close_user_apps(closer, timeout_seconds, should_stop=should_stop)
        except Exception as exc:
            self._close_apps_last_result = f"失败：{exc}"
            self._log_from_any_thread(f"优雅关闭应用失败：{exc}")
            self._invoke_on_controller_thread(self.closeAppsChanged.emit)
            return
        self._close_apps_last_result = self._format_close_apps_result(result)
        self._invoke_on_controller_thread(self.closeAppsChanged.emit)
        self._log_from_any_thread(f"优雅关闭应用：{result.message}")
        requested_titles = list(getattr(result, "requested_titles", []) or [])
        if requested_titles:
            self._log_from_any_thread(f"已请求关闭：{self._summarize_titles(requested_titles)}")
        request_failed_titles = list(getattr(result, "request_failed_titles", []) or [])
        if request_failed_titles:
            self._log_from_any_thread(f"关闭请求失败：{self._summarize_titles(request_failed_titles)}")
        remaining_titles = list(getattr(result, "remaining_titles", []) or [])
        if remaining_titles:
            self._log_from_any_thread(f"仍未退出：{self._summarize_titles(remaining_titles)}")

    def _format_close_apps_result(self, result):
        request_failed = len(getattr(result, "request_failed_titles", []) or [])
        return (
            f"可用：{self._yes_no(result.available)} · 已请求：{result.attempted} · "
            f"已关闭：{result.closed} · 仍在运行：{result.remaining} · "
            f"请求失败：{request_failed} · 已取消：{self._yes_no(result.cancelled)} · "
            f"结果：{result.message}"
        )

    def _summarize_titles(self, titles, limit=8):
        clean_titles = [str(title) for title in titles if str(title)]
        shown = "、".join(clean_titles[:limit])
        extra = len(clean_titles) - limit
        if extra > 0:
            return f"{shown} 等 {extra} 个"
        return shown

    def _begin_power_action(self):
        with self._power_action_lock:
            if self._power_action_in_progress:
                return False
            self._power_action_in_progress = True
        self.powerActionProgressChanged.emit()
        return True

    def _finish_power_action(self):
        changed = False
        with self._power_action_lock:
            if self._power_action_in_progress:
                self._power_action_in_progress = False
                changed = True
            if self._power_action_progress_text:
                self._power_action_progress_text = ""
                changed = True
        if changed:
            self._invoke_on_controller_thread(self.powerActionProgressChanged.emit)

    def _set_power_action_progress_text(self, text):
        changed = False
        with self._power_action_lock:
            text = str(text or "")
            if self._power_action_progress_text != text:
                self._power_action_progress_text = text
                changed = True
        if changed:
            self._invoke_on_controller_thread(self.powerActionProgressChanged.emit)

    def _set_close_apps_skip_event(self, event, expected=None):
        changed = False
        with self._power_action_lock:
            if expected is not None and self._close_apps_skip_event is not expected:
                return
            if self._close_apps_skip_event is not event:
                self._close_apps_skip_event = event
                changed = True
        if changed:
            self._invoke_on_controller_thread(self.powerActionProgressChanged.emit)

    def _notify_power_action_complete(self, completion, success, error):
        if completion is None:
            return
        self._invoke_on_controller_thread(lambda: completion(success, error))

    def _log_from_any_thread(self, message):
        if QThread.currentThread() == self.thread():
            self._add_log(message)
        else:
            self._workerLogRequested.emit(str(message))

    def _invoke_on_controller_thread(self, callback):
        if QThread.currentThread() == self.thread():
            callback()
        else:
            self._workerCallbackRequested.emit(callback)

    def _run_worker_callback(self, callback):
        try:
            callback()
        except Exception as exc:
            self._add_log(f"后台任务回调失败：{exc}")

    def _maybe_close_apps(self, action=None):
        """Gracefully ask running apps to close before a session-ending action.

        Mirrors a normal manual shutdown (apps get a chance to save). Honors
        安全验证模式只记录将要关闭的应用，不会真正关闭它们。
        """
        action = self._selected_action if action is None else action
        if not self._close_apps_before_action or not self._close_apps_supported(action):
            return
        try:
            closer = self._get_app_closer()
        except Exception as exc:
            self._add_log(f"优雅关闭应用不可用：{exc}")
            return
        if self._dry_run:
            try:
                windows = list(closer.list_app_windows())
            except Exception as exc:
                self._add_log(f"安全验证：枚举待关闭应用失败：{exc}")
                return
            if not windows:
                self._add_log("安全验证：没有需要优雅关闭的应用")
                return
            names = "、".join(w.title for w in windows[:8])
            suffix = " 等" if len(windows) > 8 else ""
            self._add_log(f"安全验证：将优雅关闭 {len(windows)} 个应用：{names}{suffix}")
            return
        self._close_apps_with_closer(closer, self._close_apps_timeout_seconds)

    def _check_process_running(self, process_name):
        self._last_process_check_error = ""
        try:
            return bool(self._process_checker(process_name))
        except Exception as exc:
            self._last_process_check_error = exception_text(exc)
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
            self._last_process_check_error = exception_text(exc)
            return False
        if completed.returncode != 0:
            message = (
                completed.stderr
                or completed.stdout
                or f"进程列表命令退出码 {completed.returncode}"
            ).strip()
            self._last_process_check_error = message
            return False
        return any(line.lower().startswith(f'"{clean_name}"') for line in completed.stdout.splitlines())

    def _record_history(self, event, action, source, task_id, message):
        self._history_settings["taskHistoryLimit"] = self._history_limit
        source_label = self.taskSourceLabel(source)
        display_message = message if message.startswith(source_label) else f"{source_label}：{message}"
        append_history_event(
            self._history_settings,
            HistoryEvent(
                datetime.now().isoformat(timespec="seconds"),
                event,
                action,
                source,
                "dry-run" if self._dry_run else "live",
                task_id or "",
                display_message,
            ),
        )
        self._save_settings()
        self.historyChanged.emit()

    def _trim_history_to_limit(self):
        rows = self._history_settings.setdefault("taskHistory", [])
        if len(rows) > self._history_limit:
            del rows[: len(rows) - self._history_limit]

    def _filtered_logs(self):
        if self._log_filter == "all":
            return list(self._logs)
        return [entry for entry in self._logs if self._log_entry_kind(entry) == self._log_filter]

    def _log_entry_kind(self, entry):
        lower = str(entry or "").lower()
        if any(marker in lower for marker in ("warning", "warn", "danger", "警告")):
            return "warning"
        if any(marker in lower for marker in ("failed", "error", "失败", "错误", "不可用", "拒绝")):
            return "error"
        return "info"

    def _copy_text(self, text):
        self._last_copied_text = str(text or "")
        clipboard_ok = self._write_clipboard_text(self._last_copied_text)
        status = "已复制" if clipboard_ok else "已准备"
        self._copy_status_text = f"{status}：{len(self._last_copied_text)} 个字符"
        self.logTextChanged.emit()

    def _write_clipboard_text(self, text):
        if self._clipboard_writer is not None:
            self._clipboard_writer(text)
            return True
        try:
            from PySide6.QtGui import QGuiApplication
            app = QGuiApplication.instance()
            if app is None or not isinstance(app, QGuiApplication):
                return False
            clipboard = app.clipboard()
            if clipboard is None:
                return False
            clipboard.setText(text)
            return True
        except Exception:
            return False

    def _add_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._logs.append(f"{timestamp} · {message}")
        self._logs = self._logs[-24:]
        self.logTextChanged.emit()

    def _strip_log_timestamp(self, entry):
        text = str(entry or "")
        marker = " · "
        return text.split(marker, 1)[1] if marker in text else text

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
            "closeAppsBeforeAction": self._close_apps_before_action,
            "closeAppsTimeoutSeconds": self._close_apps_timeout_seconds,
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
            "idleTriggerEnabled": self._idle_trigger_enabled,
            "idleMinutes": self._idle_minutes,
            "idlePollSeconds": self._idle_poll_seconds,
            "idleAction": self._idle_action,
            "musicAutoplayEnabled": self._music_autoplay_enabled,
            "musicVolume": self._music_volume,
            "musicFolder": self._music_folder,
            "musicCurrentIndex": self._music_current_index,
            "musicPlaybackMode": self._music_playback_mode,
            "reminderEnabled": self._reminder_enabled,
            "reminderMinutesCsv": self._reminder_minutes_csv,
            "snoozeMinutes": self._snooze_minutes_value,
            "taskQueue": self._scheduler.to_settings(),
            "taskHistory": self._history_settings.get("taskHistory", []),
            "taskHistoryLimit": self._history_limit,
            "windowsNotificationsEnabled": self._windows_notifications_enabled,
            "startWithWindows": self._start_with_windows,
            "startMinimizedToTray": self._start_minimized_to_tray,
            "firstRunSafetyGuideShown": self._first_run_safety_guide_shown,
            "trayCloseHintShown": self._tray_close_hint_shown,
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
        return bool(app and QCoreApplication.applicationName() == "定时关机助手")

    def _pick_music_folder(self):
        return QFileDialog.getExistingDirectory(None, "选择音乐文件夹", self.musicFolder or str(Path(__file__).resolve().parents[1]))

    def _now(self):
        return datetime.now()

    def _reminder_minutes(self):
        values = []
        for token in self._reminder_minutes_csv.split(","):
            try:
                value = int(str(token).strip())
            except ValueError:
                continue
            if value > 0:
                values.append(value)
        unique = sorted(set(values), reverse=True)
        return unique or [10, 5, 1]

    def _coerce_music_playback_mode(self, value):
        value = str(value or "")
        if value in {"sequence", "list_loop", "single_loop"}:
            return value
        return "sequence"

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

    def _coerce_close_apps_timeout(self, value):
        return min(
            self.CLOSE_APPS_MAX_TIMEOUT_SECONDS,
            self._coerce_int(value, 20, minimum=1),
        )

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
