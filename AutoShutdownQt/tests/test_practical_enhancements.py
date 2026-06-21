from datetime import timedelta
import contextlib
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
sys.path.insert(0, str(APP_DIR))

from tests.qt_test_env import ensure_qt_modules
ensure_qt_modules()

from PySide6.QtCore import QCoreApplication

from controller import AppController
from idle_service import IdleSample
import network_service
from network_service import NetworkReader, NetworkSample, compute_speed
from settings_service import default_settings, load_settings, save_settings


class FakeIdleReader:
    def __init__(self, samples):
        self.samples = list(samples)

    def sample(self):
        if not self.samples:
            return IdleSample(False, 0, "no more samples")
        return self.samples.pop(0)


class StaticIdleReader:
    def __init__(self, idle_seconds):
        self._idle_seconds = int(idle_seconds)

    def sample(self):
        return IdleSample(True, self._idle_seconds, "")


class FakeNetworkReader:
    def __init__(self, samples):
        self.samples = list(samples)

    def sample(self):
        if not self.samples:
            return NetworkSample(False, message="no more samples")
        return self.samples.pop(0)


class DelayedMonitorExecutor:
    def __init__(self):
        self.jobs = []

    def submit(self, work, callback):
        self.jobs.append((work, callback))

    def run_next(self):
        work, callback = self.jobs.pop(0)
        callback(work())


class ImmediateMonitorExecutor:
    def submit(self, work, callback):
        callback(work())


class FakeSignal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def emit(self):
        for callback in list(self.callbacks):
            callback()


class FakeMusicService:
    def __init__(self, available=True, title="demo.mp3", tracks=None):
        self.available = available
        self.title = title
        self.playing = False
        self.tracks = tracks or [Path("C:/Music/demo.mp3")]
        self.current_index = 0 if self.tracks else -1
        self.folder = Path("C:/Music")
        self.position_ms = 0
        self.duration_ms = 0
        self.position_text = "00:00"
        self.duration_text = "00:00"
        self.play_calls = 0
        self.pause_calls = 0
        self.stop_calls = 0
        self.volume_values = []
        self.playback_mode = "sequence"
        self.next_calls = 0
        self.previous_calls = 0
        self.selected = []
        self.seek_values = []
        self.folders = []
        self.playbackChanged = FakeSignal()
        self.errorChanged = FakeSignal()

    def play(self):
        self.play_calls += 1
        if not self.available:
            return False
        self.playing = True
        return True

    def pause(self):
        self.pause_calls += 1
        self.playing = False

    def stop(self):
        self.stop_calls += 1
        self.playing = False

    def set_volume(self, value):
        self.volume_values.append(value)

    def select_track(self, index, autoplay=False):
        self.selected.append((index, autoplay))
        if index < 0 or index >= len(self.tracks):
            return False
        self.current_index = index
        self.title = self.tracks[index].name
        if autoplay:
            self.playing = True
        return True

    def next_track(self):
        self.next_calls += 1
        if not self.tracks:
            return False
        self.current_index = (self.current_index + 1) % len(self.tracks)
        self.title = self.tracks[self.current_index].name
        return True

    def previous_track(self):
        self.previous_calls += 1
        if not self.tracks:
            return False
        self.current_index = (self.current_index - 1) % len(self.tracks)
        self.title = self.tracks[self.current_index].name
        return True

    def seek(self, position_ms):
        self.seek_values.append(position_ms)
        self.position_ms = position_ms
        self.position_text = "01:05"

    def set_folder(self, folder, current_index=0):
        self.folders.append((Path(folder), current_index))
        self.folder = Path(folder)
        self.current_index = current_index




class FakeNotificationService:
    def __init__(self):
        self.reminders = []

    def show_reminder(self, title, body):
        self.reminders.append((title, body))
        return True


class FakeStartupService:
    def __init__(self):
        self.enabled_values = []

    def set_enabled(self, enabled):
        self.enabled_values.append(bool(enabled))
        return True

class PracticalEnhancementsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def _workspace_scratch(self, name):
        target = ROOT / "test-tmp" / name
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        target.mkdir(parents=True, exist_ok=True)
        self.addCleanup(lambda: shutil.rmtree(target, ignore_errors=True))
        return target

    def test_settings_round_trip_merges_defaults(self):
        root = self._workspace_scratch("practical-settings-merge")
        path = root / "settings.json"
        data = default_settings()
        data.update({
            "dryRun": False,
            "selectedAction": "sleep",
            "scriptPath": "C:/demo.bat",
            "networkDownloadThresholdKbps": 12.5,
        })

        save_settings(data, path)
        loaded = load_settings(path)

        self.assertFalse(loaded["dryRun"])
        self.assertEqual(loaded["selectedAction"], "sleep")
        self.assertEqual(loaded["scriptPath"], "C:/demo.bat")
        self.assertEqual(loaded["networkDownloadThresholdKbps"], 12.5)
        self.assertIn("networkIdleSeconds", loaded)

    def test_default_settings_include_versioned_task_queue(self):
        settings = default_settings()

        self.assertIn("taskQueue", settings)
        self.assertEqual(settings["taskQueue"], {"version": 1, "tasks": []})

    def test_default_settings_include_music_preferences(self):
        settings = default_settings()

        self.assertTrue(settings["musicAutoplayEnabled"])
        self.assertEqual(settings["musicVolume"], 70)
        self.assertEqual(settings["musicFolder"], "")
        self.assertEqual(settings["musicCurrentIndex"], 0)
        self.assertEqual(settings["musicPlaybackMode"], "sequence")

    def test_default_settings_include_reminder_preferences(self):
        settings = default_settings()

        self.assertTrue(settings["reminderEnabled"])
        self.assertEqual(settings["reminderMinutesCsv"], "10,5,1")
        self.assertEqual(settings["snoozeMinutes"], 15)

    def test_default_settings_include_2_5_background_preferences(self):
        settings = default_settings()

        self.assertTrue(settings["windowsNotificationsEnabled"])
        self.assertFalse(settings["startWithWindows"])
        self.assertFalse(settings["startMinimizedToTray"])
        self.assertEqual(settings["taskHistory"], [])
        self.assertEqual(settings["taskHistoryLimit"], 500)

    def test_default_settings_include_idle_trigger_preferences(self):
        settings = default_settings()

        self.assertFalse(settings["idleTriggerEnabled"])
        self.assertEqual(settings["idleMinutes"], 30)
        self.assertEqual(settings["idlePollSeconds"], 10)
        self.assertEqual(settings["idleAction"], "shutdown")

    def test_default_settings_include_3_2_safety_acknowledgements(self):
        settings = default_settings()

        self.assertFalse(settings["firstRunSafetyGuideShown"])
        self.assertFalse(settings["trayCloseHintShown"])

    def test_controller_persists_3_2_safety_acknowledgements(self):
        controller = AppController()

        self.assertFalse(controller.firstRunSafetyGuideShown)
        self.assertFalse(controller.trayCloseHintShown)

        controller.acknowledgeFirstRunSafetyGuide()
        controller.acknowledgeTrayCloseHint()

        self.assertTrue(controller.firstRunSafetyGuideShown)
        self.assertTrue(controller.trayCloseHintShown)
        saved = controller._settings_snapshot()
        self.assertTrue(saved["firstRunSafetyGuideShown"])
        self.assertTrue(saved["trayCloseHintShown"])

    def test_controller_exposes_configurable_idle_trigger_preferences(self):
        controller = AppController(idle_reader=StaticIdleReader(0))

        self.assertFalse(controller.idleTriggerEnabled)
        self.assertEqual(controller.idleMinutes, 30)
        self.assertEqual(controller.idlePollSeconds, 10)
        self.assertEqual(controller.idleAction, "shutdown")
        self.assertEqual(controller.idleTriggerStatus, "未启动")

        controller.idleTriggerEnabled = True
        controller.idleMinutes = 45
        controller.idlePollSeconds = 15
        controller.idleAction = "sleep"

        self.assertTrue(controller.idleTriggerEnabled)
        self.assertEqual(controller.idleMinutes, 45)
        self.assertEqual(controller.idlePollSeconds, 15)
        self.assertEqual(controller.idleAction, "sleep")

    def test_idle_trigger_adds_queue_task_when_idle_threshold_is_reached(self):
        reader = FakeIdleReader([IdleSample(True, 0, ""), IdleSample(True, 1800, "")])
        controller = AppController(idle_reader=reader)
        controller.idleMinutes = 30
        controller.idleAction = "sleep"

        controller.startIdleTrigger()
        controller._poll_idle_trigger()

        self.assertFalse(controller.idleTriggerActive)
        self.assertIn("空闲触发", controller.queueText)
        self.assertIn("sleep", controller.queueRowsJson)
        self.assertIn("已空闲 30 / 30 分钟", controller.idleTriggerStatus)

    def test_idle_trigger_queue_task_executes_on_next_tick(self):
        reader = FakeIdleReader([IdleSample(True, 0, ""), IdleSample(True, 1800, "")])
        controller = AppController(idle_reader=reader)
        controller.dryRun = False
        controller.scriptEnabled = False
        power_calls = []
        controller._power_executor = lambda action, force: power_calls.append((action, force)) or True
        controller.idleMinutes = 30
        controller.idleAction = "sleep"

        controller.startIdleTrigger()
        controller._poll_idle_trigger()
        controller._on_tick()

        self.assertEqual(power_calls, [("sleep", False)])

    def test_idle_trigger_does_not_emit_when_polled_status_is_unchanged(self):
        reader = FakeIdleReader([IdleSample(True, 120, ""), IdleSample(True, 120, "")])
        controller = AppController(idle_reader=reader)
        controller.idleMinutes = 30
        emissions = []

        controller.startIdleTrigger()
        controller.idleTriggerChanged.connect(lambda: emissions.append(controller.idleTriggerStatus))
        controller._poll_idle_trigger()

        self.assertEqual(emissions, [])

    def test_idle_trigger_waits_when_user_is_not_idle_long_enough(self):
        reader = FakeIdleReader([IdleSample(True, 0, ""), IdleSample(True, 120, "")])
        controller = AppController(idle_reader=reader)
        controller.idleMinutes = 30

        controller.startIdleTrigger()
        controller._poll_idle_trigger()

        self.assertTrue(controller.idleTriggerActive)
        self.assertNotIn("空闲触发", controller.queueText)
        self.assertEqual(controller.idleTriggerStatus, "已空闲 2 / 30 分钟")

    def test_idle_trigger_reports_unavailable_reader(self):
        reader = FakeIdleReader([IdleSample(False, 0, "no user32")])
        controller = AppController(idle_reader=reader)

        controller.startIdleTrigger()

        self.assertFalse(controller.idleTriggerActive)
        self.assertIn("空闲检测不可用", controller.idleTriggerStatus)

    def test_controller_formats_task_source_labels(self):
        controller = AppController()

        self.assertEqual(controller.taskSourceLabel("countdown"), "手动倒计时")
        self.assertEqual(controller.taskSourceLabel("clock"), "指定时间")
        self.assertEqual(controller.taskSourceLabel("template"), "模板任务")
        self.assertEqual(controller.taskSourceLabel("process"), "进程退出触发")
        self.assertEqual(controller.taskSourceLabel("network"), "网络闲置触发")
        self.assertEqual(controller.taskSourceLabel("idle"), "空闲触发")
        self.assertEqual(controller.taskSourceLabel("queue"), "队列任务")
        self.assertEqual(controller.taskSourceLabel("reminder"), "执行前提醒")
        self.assertEqual(controller.taskSourceLabel("active-countdown"), "手动倒计时")
        unknown_label = controller.taskSourceLabel("unknown")
        self.assertEqual(unknown_label, "未知来源")
        self.assertNotIn("unknown", unknown_label)

    def test_controller_records_active_countdown_history_with_readable_source_label(self):
        controller = AppController()

        controller._record_history("cancelled", "shutdown", "active-countdown", "", "已取消当前任务")

        self.assertIn("手动倒计时：已取消当前任务", controller.historyRowsJson)
        self.assertNotIn("active-countdown：", controller.historyRowsJson)

    def test_controller_records_history_and_notifies_for_reminder(self):
        notifier = FakeNotificationService()
        controller = AppController(notification_service=notifier)
        controller.reminderMinutesCsv = "1"
        controller._remaining_seconds = 60
        controller._status = "running"

        controller._check_execution_reminders()

        self.assertEqual(notifier.reminders[0][0], "执行前提醒")
        self.assertIn("执行前提醒", controller.historyRowsJson)

    def test_controller_clear_and_export_history_slots(self):
        root = self._workspace_scratch("practical-history-export")
        target = root / "logs.txt"
        controller = AppController(log_export_path=target)
        controller._record_history("created", "shutdown", "countdown", "task-a", "created task")

        controller.exportHistory()
        controller.clearHistory()

        self.assertEqual(controller.historyRowsJson, "[]")
        self.assertTrue(target.with_name("AutoShutdownQt-history.json").exists())

    def test_controller_startup_preferences_delegate_to_service(self):
        startup = FakeStartupService()
        controller = AppController(startup_service=startup)

        controller.startWithWindows = True
        controller.startMinimizedToTray = True

        self.assertEqual(startup.enabled_values, [True])
        self.assertTrue(controller.startWithWindows)
        self.assertTrue(controller.startMinimizedToTray)

    def test_controller_records_create_snooze_cancel_and_dry_run_history(self):
        controller = AppController()

        controller.startCountdown(0, 1, 0)
        task_id = controller._scheduler.tasks[0].id
        controller._queue_reminder_task_id = task_id
        controller.snoozeCurrentTask()
        controller.cancelCurrentTask()
        controller.executeNow()

        history = controller.historyRowsJson
        self.assertIn("已加入任务队列", history)
        self.assertIn("已延后", history)
        self.assertIn("已取消当前任务", history)
        self.assertIn("安全验证", history)
        self.assertNotIn("Dry-run", history)

    def test_controller_exposes_reminder_preferences(self):
        controller = AppController()

        self.assertTrue(controller.reminderEnabled)
        self.assertEqual(controller.reminderMinutesCsv, "10,5,1")
        self.assertEqual(controller.snoozeMinutesValue, 15)

        controller.reminderEnabled = False
        controller.reminderMinutesCsv = "20, 10, 10, nope, 0, -1, 5"
        controller.snoozeMinutesValue = 30

        self.assertFalse(controller.reminderEnabled)
        self.assertEqual(controller.reminderMinutesCsv, "20, 10, 10, nope, 0, -1, 5")
        self.assertEqual(controller.snoozeMinutesValue, 30)
        self.assertEqual(controller._reminder_minutes(), [20, 10, 5])

    def test_reminder_fires_once_when_countdown_reaches_threshold(self):
        controller = AppController()
        controller.reminderMinutesCsv = "1"
        emissions = []
        controller.reminderChanged.connect(lambda: emissions.append(controller.reminderDialogTitle))
        controller._remaining_seconds = 60
        controller._status = "running"

        controller._check_execution_reminders()
        controller._check_execution_reminders()

        self.assertEqual(emissions.count("执行前提醒"), 1)
        self.assertIn("关机", controller.reminderDialogBody)
        self.assertIn("安全验证", controller.reminderDialogBody)
        self.assertNotIn("Dry-run", controller.reminderDialogBody)
        self.assertEqual(controller.reminderDialogSnoozeText, "延后 15 分钟")

    def test_reminder_body_distinguishes_real_execution_mode(self):
        controller = AppController()
        controller.dryRun = False
        controller.reminderMinutesCsv = "1"
        controller._remaining_seconds = 60
        controller._status = "running"

        controller._check_execution_reminders()

        self.assertIn("真实执行", controller.reminderDialogBody)

    def test_public_countdown_queue_shows_configured_reminder_before_due(self):
        controller = AppController()
        controller.reminderMinutesCsv = "1"
        emissions = []
        controller.reminderChanged.connect(lambda: emissions.append(controller.reminderDialogTitle))

        controller.startCountdown(0, 1, 0)
        controller._on_tick()

        self.assertIn("执行前提醒", emissions)
        self.assertIn("关机", controller.reminderDialogBody)
        self.assertIn("安全验证", controller.reminderDialogBody)
        self.assertNotIn("Dry-run", controller.reminderDialogBody)

    def test_each_queue_task_gets_its_own_reminder_thresholds(self):
        controller = AppController()
        controller.reminderMinutesCsv = "1"
        emissions = []
        controller.reminderChanged.connect(lambda: emissions.append(controller.reminderDialogTitle))
        controller.startCountdown(0, 1, 0)
        controller.startCountdown(0, 2, 0)
        first, second = controller._scheduler.tasks[0], controller._scheduler.tasks[1]

        controller._on_tick()
        first.next_run_at = controller._now()
        controller._on_tick()
        second.next_run_at = controller._now() + timedelta(seconds=60)
        controller._on_tick()

        self.assertEqual(emissions.count("执行前提醒"), 2)

    def test_cancel_current_task_removes_reminded_queue_task(self):
        controller = AppController()
        controller.reminderMinutesCsv = "1"
        controller.startCountdown(0, 1, 0)
        task_id = controller._scheduler.tasks[0].id
        controller._on_tick()

        controller.cancelCurrentTask()

        self.assertEqual(controller.queueTaskCount, 0)
        self.assertNotIn(task_id, controller.queueRowsJson)
        self.assertIn("已取消当前任务", controller.logText)

    def test_snooze_current_task_extends_active_countdown_and_resets_reminders(self):
        controller = AppController()
        controller.snoozeMinutesValue = 2
        controller._remaining_seconds = 60
        controller._status = "running"
        controller._shown_reminders.add(1)

        controller.snoozeCurrentTask()

        self.assertEqual(controller.remainingSeconds, 180)
        self.assertEqual(controller._shown_reminders, set())
        self.assertIn("已延后 2 分钟", controller.logText)

    def test_snooze_current_task_extends_next_queue_task(self):
        controller = AppController()
        controller.snoozeMinutesValue = 5
        controller.startCountdown(0, 1, 0)
        task = controller._scheduler.tasks[0]
        before = task.next_run_at

        controller.snoozeCurrentTask()

        self.assertEqual(task.next_run_at, before + timedelta(minutes=5))
        self.assertIn("已延后 5 分钟", controller.logText)

    def test_controller_exposes_music_state_and_delegates_slots(self):
        music = FakeMusicService(available=True, title="demo.mp3")
        controller = AppController(music_service=music)

        self.assertTrue(controller.musicAvailable)
        self.assertEqual(controller.musicTitle, "demo.mp3")
        self.assertTrue(controller.musicAutoplayEnabled)
        self.assertEqual(controller.musicVolume, 70)

        controller.setMusicVolume(35)
        controller.playMusic()
        self.assertTrue(controller.musicPlaying)
        controller.pauseMusic()
        self.assertFalse(controller.musicPlaying)
        controller.stopMusic()

        self.assertEqual(music.volume_values, [70, 35])
        self.assertEqual(music.play_calls, 1)
        self.assertEqual(music.pause_calls, 1)
        self.assertEqual(music.stop_calls, 1)

    def test_controller_exposes_music_playlist_and_seek_state(self):
        tracks = [Path("C:/Music/a.mp3"), Path("C:/Music/b.mp3")]
        music = FakeMusicService(title="a.mp3", tracks=tracks)
        music.duration_ms = 185000
        music.duration_text = "03:05"
        controller = AppController(music_service=music)

        self.assertEqual(Path(controller.musicFolder), Path("C:/Music"))
        self.assertIn('"title": "a.mp3"', controller.musicTracksJson)
        self.assertIn('"index": 1', controller.musicTracksJson)
        self.assertEqual(controller.musicCurrentIndex, 0)
        self.assertEqual(controller.musicPositionMs, 0)
        self.assertEqual(controller.musicDurationMs, 185000)
        self.assertEqual(controller.musicPositionText, "00:00")
        self.assertEqual(controller.musicDurationText, "03:05")

        controller.playMusicTrack(1)
        controller.seekMusic(65000)

        self.assertEqual(music.selected, [(1, True)])
        self.assertEqual(music.seek_values, [65000])
        self.assertEqual(controller.musicCurrentIndex, 1)
        self.assertEqual(controller.musicPositionMs, 65000)

    def test_controller_music_previous_next_and_playback_mode_delegate_to_service(self):
        tracks = [Path("C:/Music/a.mp3"), Path("C:/Music/b.mp3")]
        music = FakeMusicService(title="a.mp3", tracks=tracks)
        controller = AppController(music_service=music)

        self.assertEqual(controller.musicPlaybackMode, "sequence")
        controller.nextMusicTrack()
        self.assertEqual(music.next_calls, 1)
        self.assertEqual(controller.musicCurrentIndex, 1)

        controller.previousMusicTrack()
        self.assertEqual(music.previous_calls, 1)
        self.assertEqual(controller.musicCurrentIndex, 0)

        controller.setMusicPlaybackMode("list_loop")
        self.assertEqual(controller.musicPlaybackMode, "list_loop")
        self.assertEqual(music.playback_mode, "list_loop")

    def test_controller_choose_music_folder_updates_service_and_settings(self):
        root = self._workspace_scratch("practical-music-folder")
        settings_path = root / "settings.json"
        chosen_folder = root / "Music"
        chosen_folder.mkdir()
        music = FakeMusicService()
        controller = AppController(settings_path=settings_path, music_service=music)
        controller._folder_picker = lambda: str(chosen_folder)

        controller.chooseMusicFolder()
        loaded = load_settings(settings_path)

        self.assertEqual(music.folders, [(chosen_folder, 0)])
        self.assertEqual(loaded["musicFolder"], str(chosen_folder))
        self.assertEqual(loaded["musicCurrentIndex"], 0)

    def test_controller_emits_music_changed_when_service_position_changes(self):
        music = FakeMusicService()
        controller = AppController(music_service=music)
        emissions = []
        controller.musicChanged.connect(lambda: emissions.append(controller.musicPositionMs))

        music.position_ms = 42000
        music.position_text = "00:42"
        music.playbackChanged.emit()

        self.assertEqual(emissions, [42000])
        self.assertEqual(controller.musicPositionText, "00:42")

    def test_controller_startup_autoplay_obeys_setting(self):
        music = FakeMusicService()
        controller = AppController(music_service=music)

        controller.startMusicAutoplay()
        self.assertEqual(music.play_calls, 1)

        controller.musicAutoplayEnabled = False
        controller.startMusicAutoplay()
        self.assertEqual(music.play_calls, 1)

    def test_controller_does_not_mark_music_playing_when_file_missing(self):
        music = FakeMusicService(available=False, title="未找到音乐文件")
        controller = AppController(music_service=music)

        controller.playMusic()

        self.assertFalse(controller.musicAvailable)
        self.assertFalse(controller.musicPlaying)
        self.assertIn("未找到音乐文件", controller.logText)

    def test_settings_round_trip_preserves_task_queue(self):
        root = self._workspace_scratch("practical-settings-queue")
        path = root / "settings.json"
        data = default_settings()
        data["taskQueue"] = {
            "version": 1,
            "tasks": [{
                "id": "task-1",
                "name": "测试任务",
                "action": "lock",
                "forceClose": False,
                "triggerType": "countdown",
                "triggerConfig": {"seconds": 60},
                "repeatRule": "once",
                "enabled": True,
                "status": "pending",
                "createdOrder": 1,
                "nextRunAt": None,
                "lastRunAt": None,
                "lastError": "",
            }],
        }

        save_settings(data, path)
        loaded = load_settings(path)

        self.assertEqual(loaded["taskQueue"]["version"], 1)
        self.assertEqual(loaded["taskQueue"]["tasks"][0]["id"], "task-1")

    def test_start_countdown_adds_queue_task_instead_of_replacing_queue(self):
        controller = AppController()

        controller.startCountdown(0, 1, 0)
        controller.startCountdown(0, 2, 0)

        self.assertEqual(controller.queueTaskCount, 2)
        self.assertIn("倒计时 1 分钟", controller.queueText)
        self.assertIn("倒计时 2 分钟", controller.queueText)
        self.assertIn("已加入任务队列", controller.logText)

    def test_fixed_time_repeat_task_can_be_added_from_qml_slot(self):
        controller = AppController()
        controller.selectedAction = "sleep"

        controller.addFixedTimeTask("每天睡眠", 23, 0, "daily")

        self.assertEqual(controller.queueTaskCount, 1)
        self.assertIn("每天睡眠", controller.queueText)
        self.assertIn("每天", controller.queueText)

    def test_due_queue_tasks_execute_through_dry_run_boundary(self):
        controller = AppController()
        controller.startCountdown(0, 0, 1)

        controller._scheduler.get_task(controller._scheduler.tasks[0].id).next_run_at = controller._now()
        controller._on_tick()

        self.assertIn("安全验证：将执行 shutdown（强制关闭：关闭）", controller.logText)
        self.assertNotIn("[dryRun]", controller.logText)
        self.assertEqual(controller.queueTaskCount, 0)
        self.assertEqual(json.loads(controller.queueRowsJson), [])
        self.assertNotIn("completed", controller.queueText)

    def test_dry_run_execution_uses_app_log_without_console_output(self):
        controller = AppController()
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            controller.executeNow()

        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("安全验证：将执行", controller.logText)

    def test_clear_logs_keeps_status_copy_localized(self):
        controller = AppController()
        controller.clearLogs()

        self.assertIn("就绪 · 日志已清空", controller.logText)
        self.assertNotIn("READY", controller.logText)

    def test_queue_persists_when_controller_uses_settings_path(self):
        root = self._workspace_scratch("practical-queue-persist")
        path = root / "settings.json"
        first = AppController(settings_path=path)
        first.startCountdown(0, 1, 0)

        second = AppController(settings_path=path)

        self.assertEqual(second.queueTaskCount, 1)
        self.assertIn("倒计时", second.queueText)

    def test_queue_task_can_be_disabled_enabled_and_deleted(self):
        controller = AppController()
        controller.startCountdown(0, 1, 0)
        task_id = controller._scheduler.tasks[0].id

        controller.setQueueTaskEnabled(task_id, False)
        self.assertIn('"enabled": false', controller.queueRowsJson)

        controller.setQueueTaskEnabled(task_id, True)
        self.assertIn('"enabled": true', controller.queueRowsJson)

        controller.deleteQueueTask(task_id)
        self.assertEqual(controller.queueTaskCount, 0)

    def test_process_trigger_start_adds_active_queue_task(self):
        controller = AppController(monitor_executor=ImmediateMonitorExecutor())
        controller.processName = "notepad.exe"
        controller._process_checker = lambda name: True

        controller.startProcessTrigger()

        self.assertEqual(controller.queueTaskCount, 1)
        self.assertIn("process_exit", controller.queueRowsJson)
        self.assertIn("notepad.exe", controller.queueText)

    def test_start_process_trigger_defers_initial_process_check(self):
        executor = DelayedMonitorExecutor()
        controller = AppController(monitor_executor=executor)
        controller.processName = "demo.exe"
        calls = []
        controller._process_checker = lambda name: calls.append(name) or True

        controller.startProcessTrigger()

        self.assertEqual(calls, [])
        self.assertEqual(len(executor.jobs), 1)
        self.assertTrue(controller.processTriggerActive)
        self.assertIn("检测中", controller.processTriggerStatus)

    def test_network_trigger_start_adds_active_queue_task(self):
        samples = [NetworkSample(True, received_bytes=1, sent_bytes=1, monotonic_seconds=1.0)]
        controller = AppController(network_reader=FakeNetworkReader(samples), monitor_executor=ImmediateMonitorExecutor())

        controller.startNetworkTrigger()

        self.assertEqual(controller.queueTaskCount, 1)
        self.assertIn("network_idle", controller.queueRowsJson)
        self.assertIn("网络闲置", controller.queueText)

    def test_start_network_trigger_defers_initial_network_sample(self):
        executor = DelayedMonitorExecutor()
        reader = FakeNetworkReader([NetworkSample(True, received_bytes=1, sent_bytes=1, monotonic_seconds=1.0)])
        controller = AppController(network_reader=reader, monitor_executor=executor)

        controller.startNetworkTrigger()

        self.assertEqual(len(reader.samples), 1)
        self.assertEqual(len(executor.jobs), 1)
        self.assertTrue(controller.networkTriggerActive)
        self.assertIn("检测中", controller.networkTriggerStatus)

    def test_process_monitor_skips_overlapping_checks_while_pending(self):
        executor = DelayedMonitorExecutor()
        controller = AppController(monitor_executor=executor)
        controller.processName = "demo.exe"
        controller._process_checker = lambda name: True

        controller.startProcessTrigger()
        controller._poll_process_trigger()

        self.assertEqual(len(executor.jobs), 1)

    def test_network_monitor_skips_overlapping_samples_while_pending(self):
        executor = DelayedMonitorExecutor()
        reader = FakeNetworkReader([
            NetworkSample(True, received_bytes=1, sent_bytes=1, monotonic_seconds=1.0),
            NetworkSample(True, received_bytes=2, sent_bytes=2, monotonic_seconds=2.0),
        ])
        controller = AppController(network_reader=reader, monitor_executor=executor)

        controller.startNetworkTrigger()
        controller._poll_network_trigger()

        self.assertEqual(len(executor.jobs), 1)
        self.assertEqual(len(reader.samples), 2)

    def test_stale_process_check_after_stop_is_ignored(self):
        executor = DelayedMonitorExecutor()
        controller = AppController(monitor_executor=executor)
        controller.processName = "demo.exe"
        controller._process_checker = lambda name: True

        controller.startProcessTrigger()
        controller.stopProcessTrigger()
        executor.run_next()

        self.assertFalse(controller.processTriggerActive)
        self.assertEqual(controller.processTriggerStatus, "已停止")

    def test_stale_network_sample_after_stop_is_ignored(self):
        executor = DelayedMonitorExecutor()
        reader = FakeNetworkReader([NetworkSample(True, received_bytes=1, sent_bytes=1, monotonic_seconds=1.0)])
        controller = AppController(network_reader=reader, monitor_executor=executor)

        controller.startNetworkTrigger()
        controller.stopNetworkTrigger()
        executor.run_next()

        self.assertFalse(controller.networkTriggerActive)
        self.assertEqual(controller.networkTriggerStatus, "已停止")

    def test_starting_second_process_trigger_replaces_previous_process_queue_task(self):
        controller = AppController(monitor_executor=ImmediateMonitorExecutor())
        controller._process_checker = lambda name: True

        controller.processName = "first.exe"
        controller.startProcessTrigger()
        controller.processName = "second.exe"
        controller.startProcessTrigger()

        self.assertEqual(controller.queueTaskCount, 1)
        self.assertNotIn("first.exe", controller.queueText)
        self.assertIn("second.exe", controller.queueText)

    def test_stopping_process_trigger_removes_matching_queue_task(self):
        controller = AppController(monitor_executor=ImmediateMonitorExecutor())
        controller.processName = "demo.exe"
        controller._process_checker = lambda name: True

        controller.startProcessTrigger()
        controller.stopProcessTrigger()

        self.assertFalse(controller.processTriggerActive)
        self.assertNotIn("process_exit", controller.queueRowsJson)
        self.assertEqual(controller.queueTaskCount, 0)

    def test_deleting_active_process_queue_task_stops_process_monitor(self):
        controller = AppController(monitor_executor=ImmediateMonitorExecutor())
        controller.processName = "demo.exe"
        controller._process_checker = lambda name: True
        controller.startProcessTrigger()
        task_id = controller._scheduler.tasks[0].id

        controller.deleteQueueTask(task_id)

        self.assertFalse(controller.processTriggerActive)
        self.assertEqual(controller.processTriggerStatus, "已停止")
        self.assertEqual(controller.queueTaskCount, 0)

    def test_starting_second_network_trigger_replaces_previous_network_queue_task(self):
        samples = [
            NetworkSample(True, received_bytes=1, sent_bytes=1, monotonic_seconds=1.0),
            NetworkSample(True, received_bytes=2, sent_bytes=2, monotonic_seconds=2.0),
        ]
        controller = AppController(network_reader=FakeNetworkReader(samples), monitor_executor=ImmediateMonitorExecutor())

        controller.networkIdleSeconds = 60
        controller.startNetworkTrigger()
        controller.networkIdleSeconds = 120
        controller.startNetworkTrigger()

        self.assertEqual(controller.queueTaskCount, 1)
        self.assertIn("网络闲置 120 秒", controller.queueText)

    def test_stopping_network_trigger_removes_matching_queue_task(self):
        samples = [NetworkSample(True, received_bytes=1, sent_bytes=1, monotonic_seconds=1.0)]
        controller = AppController(network_reader=FakeNetworkReader(samples), monitor_executor=ImmediateMonitorExecutor())

        controller.startNetworkTrigger()
        controller.stopNetworkTrigger()

        self.assertFalse(controller.networkTriggerActive)
        self.assertNotIn("network_idle", controller.queueRowsJson)
        self.assertEqual(controller.queueTaskCount, 0)

    def test_deleting_active_network_queue_task_stops_network_monitor(self):
        samples = [NetworkSample(True, received_bytes=1, sent_bytes=1, monotonic_seconds=1.0)]
        controller = AppController(network_reader=FakeNetworkReader(samples), monitor_executor=ImmediateMonitorExecutor())
        controller.startNetworkTrigger()
        task_id = controller._scheduler.tasks[0].id

        controller.deleteQueueTask(task_id)

        self.assertFalse(controller.networkTriggerActive)
        self.assertEqual(controller.networkTriggerStatus, "已停止")
        self.assertEqual(controller.queueTaskCount, 0)

    def test_controller_saves_settings_when_persisted_properties_change(self):
        root = self._workspace_scratch("practical-controller-save")
        path = root / "settings.json"
        controller = AppController(settings_path=path)

        controller.selectedAction = "sleep"
        controller.scriptEnabled = True
        controller.scriptPath = "C:/scripts/demo.bat"
        controller.networkDownloadThresholdKbps = 8.0

        loaded = load_settings(path)
        self.assertEqual(loaded["selectedAction"], "sleep")
        self.assertTrue(loaded["scriptEnabled"])
        self.assertEqual(loaded["scriptPath"], "C:/scripts/demo.bat")
        self.assertEqual(loaded["networkDownloadThresholdKbps"], 8.0)

    def test_controller_falls_back_from_non_finite_persisted_numbers(self):
        root = self._workspace_scratch("practical-nonfinite-settings")
        path = root / "settings.json"
        path.write_text(
            """
            {
              "scriptTimeoutSeconds": Infinity,
              "processPollSeconds": Infinity,
              "networkDownloadThresholdKbps": NaN,
              "networkUploadThresholdKbps": Infinity,
              "networkIdleSeconds": Infinity,
              "networkPollSeconds": Infinity
            }
            """,
            encoding="utf-8",
        )

        controller = AppController(settings_path=path)

        self.assertEqual(controller.scriptTimeoutSeconds, 10)
        self.assertEqual(controller.processPollSeconds, 5)
        self.assertEqual(controller.networkDownloadThresholdKbps, 10.0)
        self.assertEqual(controller.networkUploadThresholdKbps, 10.0)
        self.assertEqual(controller.networkIdleSeconds, 60)
        self.assertEqual(controller.networkPollSeconds, 3)

    def test_compute_speed_reports_kbps_delta(self):
        previous = NetworkSample(True, received_bytes=1024, sent_bytes=2048, monotonic_seconds=10.0)
        current = NetworkSample(True, received_bytes=3072, sent_bytes=4096, monotonic_seconds=12.0)

        speed = compute_speed(previous, current)

        self.assertTrue(speed.available)
        self.assertAlmostEqual(speed.download_kbps, 1.0)
        self.assertAlmostEqual(speed.upload_kbps, 1.0)

    def test_compute_speed_treats_counter_reset_as_unavailable(self):
        previous = NetworkSample(True, received_bytes=4096, sent_bytes=4096, monotonic_seconds=10.0)
        current = NetworkSample(True, received_bytes=1024, sent_bytes=8192, monotonic_seconds=11.0)

        speed = compute_speed(previous, current)

        self.assertFalse(speed.available)
        self.assertIn("网络计数已重置", speed.message)
        self.assertNotIn("reset", speed.message)

    def test_network_reader_nonzero_without_output_uses_chinese_error(self):
        class Completed:
            returncode = 3
            stdout = ""
            stderr = ""

        original_run = network_service.subprocess.run
        try:
            network_service.subprocess.run = lambda *args, **kwargs: Completed()
            sample = NetworkReader(counter_provider=None).sample()
        finally:
            network_service.subprocess.run = original_run

        self.assertFalse(sample.available)
        self.assertIn("网络计数命令退出码 3", sample.message)
        self.assertNotIn("netstat failed", sample.message)

    def test_network_reader_parse_failure_uses_chinese_error(self):
        class Completed:
            returncode = 0
            stdout = "No counters here"
            stderr = ""

        original_run = network_service.subprocess.run
        try:
            network_service.subprocess.run = lambda *args, **kwargs: Completed()
            sample = NetworkReader(counter_provider=None).sample()
        finally:
            network_service.subprocess.run = original_run

        self.assertFalse(sample.available)
        self.assertIn("无法读取网络计数", sample.message)
        self.assertNotIn("network counters unavailable", sample.message)

    def test_network_reader_prefers_psutil_counters_without_netstat(self):
        class Counters:
            bytes_recv = 4096
            bytes_sent = 2048

        class Provider:
            @staticmethod
            def net_io_counters():
                return Counters()

        reader = NetworkReader(counter_provider=Provider())

        def fail_netstat(*args, **kwargs):
            raise AssertionError("netstat should not run when counters are available")

        original_run = network_service.subprocess.run
        try:
            network_service.subprocess.run = fail_netstat
            sample = reader.sample()
        finally:
            network_service.subprocess.run = original_run

        self.assertTrue(sample.available)
        self.assertEqual(sample.received_bytes, 4096)
        self.assertEqual(sample.sent_bytes, 2048)

    def test_network_idle_trigger_fires_after_sustained_low_speed(self):
        samples = [
            NetworkSample(True, received_bytes=1000, sent_bytes=1000, monotonic_seconds=1.0),
            NetworkSample(True, received_bytes=1100, sent_bytes=1100, monotonic_seconds=2.0),
            NetworkSample(True, received_bytes=1200, sent_bytes=1200, monotonic_seconds=3.0),
        ]
        controller = AppController(network_reader=FakeNetworkReader(samples), monitor_executor=ImmediateMonitorExecutor())
        controller.networkDownloadThresholdKbps = 1.0
        controller.networkUploadThresholdKbps = 1.0
        controller.networkIdleSeconds = 2
        controller.networkPollSeconds = 1

        controller.startNetworkTrigger()
        controller._poll_network_trigger()
        controller._poll_network_trigger()

        self.assertFalse(controller.networkTriggerActive)
        self.assertIn("网络闲置触发", controller.logText)
        self.assertIn("安全验证：将执行", controller.logText)
        self.assertNotIn("[dryRun]", controller.logText)

    def test_network_busy_sample_resets_idle_accumulation(self):
        samples = [
            NetworkSample(True, received_bytes=0, sent_bytes=0, monotonic_seconds=1.0),
            NetworkSample(True, received_bytes=100, sent_bytes=100, monotonic_seconds=2.0),
            NetworkSample(True, received_bytes=10_000, sent_bytes=100, monotonic_seconds=3.0),
        ]
        controller = AppController(network_reader=FakeNetworkReader(samples), monitor_executor=ImmediateMonitorExecutor())
        controller.networkDownloadThresholdKbps = 1.0
        controller.networkUploadThresholdKbps = 1.0
        controller.networkIdleSeconds = 2

        controller.startNetworkTrigger()
        controller._poll_network_trigger()
        controller._poll_network_trigger()

        self.assertTrue(controller.networkTriggerActive)
        self.assertIn("0/2 秒", controller.networkTriggerStatus)

    def test_network_unavailable_logs_and_stops_without_triggering(self):
        controller = AppController(network_reader=FakeNetworkReader([
            NetworkSample(False, message="network unavailable"),
        ]), monitor_executor=ImmediateMonitorExecutor())

        controller.startNetworkTrigger()

        self.assertFalse(controller.networkTriggerActive)
        self.assertIn("网络不可用", controller.networkTriggerStatus)
        self.assertNotIn("network unavailable", controller.networkTriggerStatus)
        self.assertNotIn("network unavailable", controller.logText)
        self.assertNotIn("[dryRun] Would execute", controller.logText)
        self.assertNotIn("安全验证：将执行", controller.logText)

    def test_network_unavailable_without_message_uses_chinese_fallback(self):
        controller = AppController(network_reader=FakeNetworkReader([
            NetworkSample(False, message=""),
        ]), monitor_executor=ImmediateMonitorExecutor())

        controller.startNetworkTrigger()

        self.assertFalse(controller.networkTriggerActive)
        self.assertIn("网络不可用", controller.networkTriggerStatus)
        self.assertIn("网络监控未启动：网络不可用", controller.logText)
        self.assertNotIn("network unavailable", controller.networkTriggerStatus)
        self.assertNotIn("network unavailable", controller.logText)

    def test_network_poll_unavailable_without_message_uses_chinese_fallback(self):
        samples = [
            NetworkSample(True, received_bytes=1, sent_bytes=1, monotonic_seconds=1.0),
            NetworkSample(False, message="", monotonic_seconds=2.0),
        ]
        controller = AppController(network_reader=FakeNetworkReader(samples), monitor_executor=ImmediateMonitorExecutor())

        controller.startNetworkTrigger()
        controller._poll_network_trigger()

        self.assertFalse(controller.networkTriggerActive)
        self.assertIn("网络不可用", controller.networkTriggerStatus)
        self.assertIn("网络监控已停止：网络不可用", controller.logText)
        self.assertNotIn("network unavailable", controller.networkTriggerStatus)
        self.assertNotIn("network unavailable", controller.logText)

    def test_clear_and_export_logs(self):
        root = self._workspace_scratch("practical-clear-export-logs")
        controller = AppController(log_export_path=root / "logs.txt")
        controller.applyTaskTemplate("shutdown_15")

        controller.exportLogs()
        exported = root / "logs.txt"
        self.assertTrue(exported.exists())
        self.assertIn("15 分钟后关机", exported.read_text(encoding="utf-8"))

        controller.clearLogs()
        self.assertNotIn("15 分钟后关机", controller.logText)
        self.assertIn("日志已清空", controller.logText)

    def test_log_summary_reports_recent_activity_and_failure(self):
        controller = AppController()

        self.assertIn("1", controller.logSummaryText)

        controller._add_log("plain activity")
        controller._add_log("power action failed: power boom")

        self.assertIn("3", controller.logSummaryText)
        self.assertIn("power boom", controller.logSummaryText)
        self.assertIn("日志摘要", controller.diagnosticText)

    def test_log_category_summary_counts_info_warning_and_errors(self):
        controller = AppController()

        controller._add_log("plain info")
        controller._add_log("warning: check script path")
        controller._add_log("power action failed: power boom")
        controller._add_log("警告：脚本路径可能不可用")
        controller._add_log("电源动作执行失败：系统拒绝")

        self.assertIn("信息=", controller.logCategorySummaryText)
        self.assertIn("警告=2", controller.logCategorySummaryText)
        self.assertIn("错误=2", controller.logCategorySummaryText)
        self.assertIn("日志分类", controller.diagnosticText)
        self.assertNotIn("Log categories", controller.diagnosticText)

    def test_script_path_validation_and_open_folder(self):
        root = self._workspace_scratch("practical-script-open-folder")
        script = root / "demo.bat"
        script.write_text("echo demo", encoding="utf-8")
        opened = []
        controller = AppController(open_folder=lambda path: opened.append(Path(path)))
        controller.scriptPath = str(script)

        controller.validateScriptPath()
        controller.openScriptFolder()

        self.assertIn("脚本路径有效", controller.logText)
        self.assertEqual(opened, [script.parent])

    def test_starting_new_countdown_adds_another_queue_task(self):
        controller = AppController()

        controller.startCountdown(0, 10, 0)
        controller.startCountdown(0, 1, 30)

        self.assertEqual(controller.queueTaskCount, 2)
        self.assertIn("倒计时 10 分钟", controller.queueText)
        self.assertIn("倒计时 90 秒", controller.queueText)
        self.assertIn("已加入任务队列", controller.logText)

    def test_starting_fixed_time_adds_queue_task_after_countdown(self):
        controller = AppController()

        controller.startCountdown(0, 10, 0)
        controller.startFixedTime(23, 59)

        self.assertEqual(controller.queueTaskCount, 2)
        self.assertIn("倒计时 10 分钟", controller.queueText)
        self.assertIn("23:59", controller.queueText)
        self.assertIn("已加入任务队列", controller.logText)

    def test_start_fixed_time_rejects_out_of_range_values_without_raising(self):
        controller = AppController()

        controller.startFixedTime(99, 99)

        self.assertEqual(controller.status, "ready")
        self.assertIn("指定时间无效", controller.logText)

    def test_live_script_empty_path_blocks_power_without_running_script(self):
        controller = AppController()
        power_calls = []
        controller.dryRun = False
        controller.scriptEnabled = True
        controller.scriptPath = ""
        controller._script_runner = lambda path, timeout: self.fail("script runner should not be called")
        controller._power_executor = lambda action, force: power_calls.append((action, force))

        controller.executeNow()

        self.assertEqual(power_calls, [])
        self.assertIn("脚本路径为空", controller.logText)
        self.assertIn("已阻止电源动作", controller.logText)

    def test_live_script_missing_path_blocks_power_without_running_script(self):
        root = self._workspace_scratch("practical-missing-live-script")
        controller = AppController()
        missing_script = root / "missing-before-shutdown.bat"
        power_calls = []
        controller.dryRun = False
        controller.scriptEnabled = True
        controller.scriptPath = str(missing_script)
        controller._script_runner = lambda path, timeout: self.fail("script runner should not be called")
        controller._power_executor = lambda action, force: power_calls.append((action, force))

        controller.executeNow()

        self.assertEqual(power_calls, [])
        self.assertIn("脚本路径不存在", controller.logText)
        self.assertIn("已阻止电源动作", controller.logText)

    def test_live_test_script_uses_same_missing_path_preflight(self):
        root = self._workspace_scratch("practical-missing-test-script")
        controller = AppController()
        missing_script = root / "missing-test-script.bat"
        controller.dryRun = False
        controller.scriptEnabled = True
        controller.scriptPath = str(missing_script)
        controller._script_runner = lambda path, timeout: self.fail("script runner should not be called")

        controller.testScript()

        self.assertIn("脚本路径不存在", controller.logText)

    def test_live_script_runner_receives_normalized_path(self):
        root = self._workspace_scratch("practical-script-runner")
        script = root / "before-shutdown.bat"
        script.write_text("echo ok", encoding="utf-8")
        calls = []
        controller = AppController()
        controller.dryRun = False
        controller.scriptEnabled = True
        controller.scriptPath = f"  {script}  "
        controller._script_runner = lambda path, timeout: calls.append(path) or type("Result", (), {
            "ok": True,
            "message": "脚本执行成功",
        })()
        controller._power_executor = lambda action, force: None

        controller.executeNow()

        self.assertEqual(calls, [str(script)])

    def test_power_executor_exception_is_logged_without_propagating(self):
        controller = AppController()
        controller.dryRun = False
        controller.scriptEnabled = False

        def failing_power_executor(action, force):
            raise RuntimeError("power boom")

        controller._power_executor = failing_power_executor

        controller.executeNow()

        self.assertIn("立即执行：执行", controller.logText)
        self.assertIn("电源动作执行失败：power boom", controller.logText)

    def test_power_executor_false_return_is_logged_as_failure(self):
        controller = AppController()
        controller.dryRun = False
        controller.scriptEnabled = False
        controller._power_executor = lambda action, force: False

        controller.executeNow()

        self.assertIn("电源动作执行失败", controller.logText)

    def test_falsey_injected_power_executor_is_still_used(self):
        class FalseyExecutor:
            def __init__(self):
                self.calls = []

            def __bool__(self):
                return False

            def __call__(self, action, force):
                self.calls.append((action, force))

        executor = FalseyExecutor()
        controller = AppController()
        controller.dryRun = False
        controller.scriptEnabled = False
        controller._power_executor = executor

        controller.executeNow()

        self.assertEqual(executor.calls, [("shutdown", False)])

    def test_process_trigger_checker_exception_fails_closed_on_start(self):
        controller = AppController(monitor_executor=ImmediateMonitorExecutor())
        power_calls = []
        controller.processName = "demo.exe"
        controller._power_executor = lambda action, force: power_calls.append((action, force))

        def failing_checker(name):
            raise RuntimeError("tasklist boom")

        controller._process_checker = failing_checker

        controller.startProcessTrigger()

        self.assertFalse(controller.processTriggerActive)
        self.assertEqual(power_calls, [])
        self.assertIn("进程检测失败", controller.processTriggerStatus)
        self.assertIn("tasklist boom", controller.logText)

    def test_process_trigger_checker_exception_fails_closed_during_poll(self):
        controller = AppController(monitor_executor=ImmediateMonitorExecutor())
        power_calls = []
        controller.processName = "demo.exe"
        controller._power_executor = lambda action, force: power_calls.append((action, force))
        calls = {"count": 0}

        def checker(name):
            calls["count"] += 1
            if calls["count"] == 1:
                return True
            raise RuntimeError("poll boom")

        controller._process_checker = checker

        controller.startProcessTrigger()
        controller._poll_process_trigger()

        self.assertFalse(controller.processTriggerActive)
        self.assertEqual(power_calls, [])
        self.assertIn("进程检测失败", controller.processTriggerStatus)
        self.assertIn("poll boom", controller.logText)

    def test_process_trigger_checker_empty_exception_message_fails_closed(self):
        controller = AppController(monitor_executor=ImmediateMonitorExecutor())
        controller.processName = "demo.exe"
        controller._process_checker = lambda name: (_ for _ in ()).throw(RuntimeError())

        controller.startProcessTrigger()

        self.assertFalse(controller.processTriggerActive)
        self.assertIn("进程检测失败", controller.processTriggerStatus)

    def test_tasklist_nonzero_return_code_fails_closed(self):
        controller = AppController()

        class Completed:
            returncode = 1
            stdout = ""
            stderr = "tasklist unavailable"

        original_run = subprocess.run
        try:
            subprocess.run = lambda *args, **kwargs: Completed()
            self.assertFalse(controller._check_process_running("demo.exe"))
        finally:
            subprocess.run = original_run

        self.assertIn("tasklist unavailable", controller._last_process_check_error)

    def test_tasklist_nonzero_without_output_uses_chinese_error(self):
        controller = AppController()

        class Completed:
            returncode = 7
            stdout = ""
            stderr = ""

        original_run = subprocess.run
        try:
            subprocess.run = lambda *args, **kwargs: Completed()
            self.assertFalse(controller._check_process_running("demo.exe"))
        finally:
            subprocess.run = original_run

        self.assertIn("进程列表命令退出码 7", controller._last_process_check_error)
        self.assertNotIn("tasklist exited", controller._last_process_check_error)

    def test_process_trigger_keeps_original_process_name_while_active(self):
        controller = AppController(monitor_executor=ImmediateMonitorExecutor())
        power_calls = []
        seen_names = []
        controller.processName = "demo.exe"
        controller._power_executor = lambda action, force: power_calls.append((action, force))

        def checker(name):
            seen_names.append(name)
            return True

        controller._process_checker = checker

        controller.startProcessTrigger()
        controller.processName = "other.exe"
        controller._poll_process_trigger()

        self.assertTrue(controller.processTriggerActive)
        self.assertEqual(power_calls, [])
        self.assertEqual(seen_names, ["demo.exe", "demo.exe"])

    def test_controller_restarts_scheduler_timer_for_loaded_pending_tasks(self):
        root = self._workspace_scratch("practical-loaded-pending")
        path = root / "settings.json"
        first = AppController(settings_path=path)
        first.startCountdown(0, 1, 0)

        second = AppController(settings_path=path)

        self.assertTrue(second._timer.isActive())

    def test_controller_does_not_restart_scheduler_timer_for_loaded_completed_tasks(self):
        root = self._workspace_scratch("practical-loaded-completed")
        path = root / "settings.json"
        first = AppController(settings_path=path)
        first.startCountdown(0, 1, 0)
        task_id = first._scheduler.tasks[0].id
        first._scheduler.mark_executed(task_id, success=True)
        first._save_settings()

        second = AppController(settings_path=path)

        self.assertFalse(second._timer.isActive())

    def test_due_queue_task_records_failed_power_action(self):
        controller = AppController()
        controller.dryRun = False
        controller.scriptEnabled = False
        controller._power_executor = lambda action, force: False
        controller.startCountdown(0, 0, 1)
        task = controller._scheduler.tasks[0]
        task.next_run_at = controller._now()

        controller._on_tick()

        self.assertIn("失败", controller.queueText)
        self.assertNotIn("failed", controller.queueText)
        self.assertIn("系统拒绝或命令返回失败", controller.queueText)

    def test_due_queue_task_records_failed_power_action_exception(self):
        controller = AppController()
        controller.dryRun = False
        controller.scriptEnabled = False

        def failing_power_executor(action, force):
            raise RuntimeError("power boom")

        controller._power_executor = failing_power_executor
        controller.startCountdown(0, 0, 1)
        task = controller._scheduler.tasks[0]
        task.next_run_at = controller._now()

        controller._on_tick()

        self.assertIn("失败", controller.queueText)
        self.assertNotIn("failed", controller.queueText)
        self.assertIn("power boom", controller.queueText)

    def test_queue_summary_reports_empty_failed_and_successfully_removed_once_states(self):
        controller = AppController()

        self.assertTrue(controller.queueSummaryText)

        controller.dryRun = False
        controller.scriptEnabled = False
        controller._power_executor = lambda action, force: False
        controller.startCountdown(0, 0, 1)
        failed_task = controller._scheduler.tasks[0]
        failed_task.next_run_at = controller._now()

        controller._on_tick()

        self.assertIn("1", controller.queueSummaryText)
        self.assertIn("队列摘要", controller.diagnosticText)
        self.assertNotIn("Queue summary", controller.diagnosticText)

        controller.deleteQueueTask(failed_task.id)
        controller.dryRun = True
        controller.startCountdown(0, 0, 1)
        completed_task = controller._scheduler.tasks[0]
        completed_task.next_run_at = controller._now()

        controller._on_tick()

        self.assertEqual(controller.queueTaskCount, 0)
        self.assertEqual(json.loads(controller.queueRowsJson), [])
        self.assertNotIn("completed", controller.queueText)

    def test_queue_summary_uses_localized_fallback_for_unknown_statuses(self):
        class FakeQueueRowsScheduler:
            def __init__(self, rows):
                self._rows = rows

            def rows(self):
                return list(self._rows)

        controller = AppController()
        controller._scheduler = FakeQueueRowsScheduler([
            {"status": "legacy_state", "lastError": ""},
            {"lastError": ""},
        ])

        summary = controller.getQueueSummaryText()

        self.assertIn("未知状态 2", summary)
        self.assertNotIn("legacy_state", summary)
        self.assertNotIn("unknown", summary)

    def test_diagnostic_text_includes_key_runtime_state(self):
        controller = AppController()
        controller.selectedAction = "sleep"
        controller.scriptEnabled = True
        controller.scriptPath = "C:/demo.bat"

        diagnostics = controller.diagnosticText

        self.assertIn("定时关机助手 4.0 诊断信息", diagnostics)
        self.assertIn("安全验证：开启", diagnostics)
        self.assertNotIn("Dry-run", diagnostics)
        self.assertNotIn("Diagnostics", diagnostics)
        self.assertIn("动作：sleep（睡眠）", diagnostics)
        self.assertIn("脚本启用：是", diagnostics)
        self.assertIn("进程触发器", diagnostics)
        self.assertIn("网络触发器", diagnostics)
        self.assertIn("空闲触发器", diagnostics)
        self.assertNotIn("Action:", diagnostics)
        self.assertNotIn("Script enabled", diagnostics)
        self.assertNotIn("Process trigger", diagnostics)

    def test_safety_and_trigger_health_summaries_are_visible_in_diagnostics(self):
        controller = AppController()
        controller.scriptEnabled = True
        controller.scriptPath = "C:/demo.bat"
        controller.closeAppsBeforeAction = True

        self.assertIn("安全摘要", controller.safetySummaryText)
        self.assertIn("模式=安全验证", controller.safetySummaryText)
        self.assertNotIn("Dry-run", controller.safetySummaryText)
        self.assertNotIn("Safety summary", controller.safetySummaryText)
        self.assertIn("脚本=开启", controller.safetySummaryText)
        self.assertIn("关机前关闭应用=开启", controller.safetySummaryText)
        self.assertIn("触发器状态", controller.triggerHealthSummaryText)
        self.assertIn("进程=空闲", controller.triggerHealthSummaryText)
        self.assertIn("网络=空闲", controller.triggerHealthSummaryText)
        self.assertIn("空闲=空闲", controller.triggerHealthSummaryText)
        self.assertIn("安全摘要", controller.diagnosticText)
        self.assertIn("触发器状态", controller.diagnosticText)
        self.assertNotIn("Trigger health", controller.diagnosticText)

    def test_export_logs_includes_diagnostics_header(self):
        root = self._workspace_scratch("practical-export-logs")
        target = root / "logs.txt"
        controller = AppController(log_export_path=target)
        controller.applyTaskTemplate("shutdown_15")

        controller.exportLogs()
        exported = target.read_text(encoding="utf-8")

        self.assertIn("=== 诊断信息 ===", exported)
        self.assertIn("定时关机助手 4.0", exported)
        self.assertIn("=== 最近日志 ===", exported)
        self.assertIn("15 分钟后关机", exported)

    def test_export_diagnostics_writes_neighbor_file(self):
        root = self._workspace_scratch("practical-export-diagnostics")
        log_target = root / "logs.txt"
        controller = AppController(log_export_path=log_target)

        controller.exportDiagnostics()
        diagnostics_target = root / "logs-diagnostics.txt"

        self.assertTrue(diagnostics_target.exists())
        self.assertIn("定时关机助手 4.0", diagnostics_target.read_text(encoding="utf-8"))
        self.assertIn("诊断已导出", controller.logText)

    def test_request_dry_run_change_logs_live_mode_warning(self):
        controller = AppController()

        controller.requestDryRunChange(False)

        self.assertFalse(controller.dryRun)
        self.assertIn("真实执行模式已开启", controller.logText)
        self.assertIn("请确认", controller.logText)

        controller.requestDryRunChange(True)

        self.assertTrue(controller.dryRun)
        self.assertIn("安全验证已开启", controller.logText)
        self.assertNotIn("Dry-run", controller.logText)

    def test_power_action_in_progress_blocks_safety_setting_changes(self):
        controller = AppController()
        controller.selectedAction = "shutdown"
        controller.forceClose = False
        controller.requestDryRunChange(True)

        with controller._power_action_lock:
            controller._power_action_in_progress = True

        controller.selectedAction = "restart"
        controller.forceClose = True
        controller.requestDryRunChange(False)

        self.assertEqual(controller.selectedAction, "shutdown")
        self.assertFalse(controller.forceClose)
        self.assertTrue(controller.dryRun)
        self.assertGreaterEqual(len(controller.logText.splitlines()), 4)

    def test_power_action_step_summary_explains_current_execution_stage(self):
        controller = AppController()

        self.assertIn("就绪", controller.powerActionStepSummaryText)
        self.assertNotIn("Ready", controller.powerActionStepSummaryText)

        with controller._power_action_lock:
            controller._power_action_in_progress = True
            controller._power_action_progress_text = "正在关闭应用"
            controller._close_apps_skip_event = object()

        self.assertIn("正在关闭应用", controller.powerActionStepSummaryText)
        self.assertIn("可跳过等待", controller.powerActionStepSummaryText)
        self.assertIn("电源动作进度", controller.diagnosticText)
        self.assertNotIn("Skip available", controller.powerActionStepSummaryText)

    def test_copy_diagnostics_records_text_for_support(self):
        controller = AppController()

        controller.copyDiagnostics()

        self.assertIn("诊断信息", controller.lastCopiedText)
        self.assertIn("安全验证", controller.lastCopiedText)
        self.assertNotIn("Dry-run", controller.lastCopiedText)
        self.assertNotIn("Diagnostics", controller.lastCopiedText)
        self.assertIn("诊断已复制", controller.logText)

    def test_copy_diagnostics_writes_clipboard_and_reports_length(self):
        copied = []
        controller = AppController(clipboard_writer=copied.append)

        controller.copyDiagnostics()

        self.assertEqual(copied, [controller.lastCopiedText])
        self.assertIn(str(len(controller.lastCopiedText)), controller.copyStatusText)
        self.assertIn("已复制", controller.copyStatusText)
        self.assertIn("字符", controller.copyStatusText)
        self.assertNotIn("Copy", controller.copyStatusText)
        self.assertNotIn("chars", controller.copyStatusText)

    def test_log_filter_text_can_show_warnings_and_errors(self):
        controller = AppController()
        controller._add_log("plain info")
        controller._add_log("warning: check script")
        controller._add_log("power action failed: boom")
        controller._add_log("警告：脚本路径可能不可用")
        controller._add_log("电源动作执行失败：系统拒绝")

        controller.setLogFilter("error")
        self.assertIn("boom", controller.filteredLogText)
        self.assertIn("系统拒绝", controller.filteredLogText)
        self.assertNotIn("plain info", controller.filteredLogText)

        controller.setLogFilter("warning")
        self.assertIn("warning: check script", controller.filteredLogText)
        self.assertIn("脚本路径", controller.filteredLogText)
        self.assertNotIn("boom", controller.filteredLogText)

        controller.setLogFilter("all")
        self.assertIn("plain info", controller.filteredLogText)

    def test_run_health_check_reports_key_runtime_checks(self):
        controller = AppController()

        controller.runHealthCheck()

        self.assertIn("健康检查", controller.healthCheckText)
        self.assertIn("脚本=", controller.healthCheckText)
        self.assertIn("关闭应用服务=", controller.healthCheckText)
        self.assertIn("队列=", controller.healthCheckText)
        self.assertIn("触发器=", controller.healthCheckText)
        self.assertIn("安全=", controller.healthCheckText)
        self.assertNotIn("script=", controller.healthCheckText)
        self.assertNotIn("closeAppsService=", controller.healthCheckText)
        self.assertIn("健康检查", controller.logText)

    def test_failed_queue_task_can_be_retried_and_copied_for_diagnostics(self):
        controller = AppController()
        calls = []
        controller.dryRun = False
        controller.scriptEnabled = False
        controller._power_executor = lambda action, force: calls.append((action, force)) or False
        controller.startCountdown(0, 0, 1)
        task = controller._scheduler.tasks[0]
        task.next_run_at = controller._now()

        controller._on_tick()
        self.assertIn("失败", controller.queueText)
        self.assertNotIn("failed", controller.queueText)

        controller.copyQueueTaskDiagnostic(task.id)
        self.assertIn(task.id, controller.lastCopiedText)
        self.assertIn("=== 队列任务诊断 ===", controller.lastCopiedText)
        self.assertIn("failed", controller.lastCopiedText)
        payload = json.loads(controller.lastCopiedText.split("\n", 1)[1])
        self.assertEqual(payload.get("actionLabel"), "关机")
        self.assertEqual(payload.get("statusLabel"), "失败")
        self.assertEqual(payload.get("forceCloseLabel"), "关闭")
        self.assertIn("倒计时", payload.get("triggerSummary", ""))
        self.assertTrue(payload.get("repeatSummary"))
        self.assertIn("队列任务诊断已复制", controller.logText)
        self.assertNotIn("Queue Task Diagnostic", controller.lastCopiedText)
        self.assertNotIn("Queue task diagnostic", controller.logText)

        controller._power_executor = lambda action, force: calls.append((action, force)) or True
        controller.retryQueueTask(task.id)

        self.assertIn("队列任务重试已完成", controller.logText)
        self.assertNotIn("Queue task retry", controller.logText)
        self.assertNotIn("Retry queue task", controller.logText)
        self.assertNotIn("completed:", controller.logText)
        self.assertEqual(controller.queueTaskCount, 0)
        self.assertNotIn("completed", controller.queueText)
        self.assertGreaterEqual(len(calls), 2)

    def test_retry_queue_task_reports_pending_task_in_chinese(self):
        controller = AppController()
        controller.startCountdown(0, 1, 0)
        task = controller._scheduler.tasks[0]

        controller.retryQueueTask(task.id)

        self.assertIn("任务未失败，无法重试", controller.logText)
        self.assertNotIn("Task is not failed", controller.logText)
        self.assertNotIn("retry skipped", controller.logText)

    def test_additional_task_templates_start_expected_actions(self):
        controller = AppController()

        controller.applyTaskTemplate("lock_5")
        self.assertEqual(controller.selectedAction, "lock")
        self.assertIn("倒计时 5 分钟", controller.queueText)
        self.assertIn("5 分钟后锁定", controller.logText)

        controller.applyTaskTemplate("sleep_10")
        self.assertEqual(controller.selectedAction, "sleep")
        self.assertIn("倒计时 10 分钟", controller.queueText)
        self.assertIn("10 分钟后睡眠", controller.logText)

        controller.applyTaskTemplate("shutdown_midnight")
        self.assertEqual(controller.selectedAction, "shutdown")
        self.assertIn("00:00", controller.queueText)
        self.assertIn("明天 00:00 关机", controller.logText)

    def test_snooze_minutes_extends_active_timed_task(self):
        controller = AppController()
        controller.startCountdown(0, 10, 0)

        controller.snoozeMinutes(5)

        self.assertIn("没有正在运行的定时任务", controller.logText)
        self.assertIn("倒计时 10 分钟", controller.queueText)

    def test_snooze_minutes_rejects_invalid_or_inactive_task(self):
        controller = AppController()

        controller.snoozeMinutes(5)
        self.assertIn("没有正在运行的定时任务", controller.logText)

        controller.startCountdown(0, 1, 0)
        controller.snoozeMinutes(0)
        self.assertIn("倒计时 1 分钟", controller.queueText)
        self.assertIn("延后时长无效", controller.logText)


if __name__ == "__main__":
    unittest.main()
