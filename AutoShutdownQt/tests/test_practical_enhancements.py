import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

from PySide6.QtCore import QCoreApplication

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
sys.path.insert(0, str(APP_DIR))

from controller import AppController
from network_service import NetworkSample, compute_speed
from settings_service import default_settings, load_settings, save_settings


class FakeNetworkReader:
    def __init__(self, samples):
        self.samples = list(samples)

    def sample(self):
        if not self.samples:
            return NetworkSample(False, message="no more samples")
        return self.samples.pop(0)


class PracticalEnhancementsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_settings_round_trip_merges_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
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

    def test_settings_round_trip_preserves_task_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
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

        self.assertIn("[dryRun] Would execute: shutdown force=False", controller.logText)
        self.assertIn("completed", controller.queueText)

    def test_queue_persists_when_controller_uses_settings_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
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
        controller = AppController()
        controller.processName = "notepad.exe"
        controller._process_checker = lambda name: True

        controller.startProcessTrigger()

        self.assertEqual(controller.queueTaskCount, 1)
        self.assertIn("process_exit", controller.queueRowsJson)
        self.assertIn("notepad.exe", controller.queueText)

    def test_network_trigger_start_adds_active_queue_task(self):
        samples = [NetworkSample(True, received_bytes=1, sent_bytes=1, monotonic_seconds=1.0)]
        controller = AppController(network_reader=FakeNetworkReader(samples))

        controller.startNetworkTrigger()

        self.assertEqual(controller.queueTaskCount, 1)
        self.assertIn("network_idle", controller.queueRowsJson)
        self.assertIn("网络闲置", controller.queueText)

    def test_starting_second_process_trigger_replaces_previous_process_queue_task(self):
        controller = AppController()
        controller._process_checker = lambda name: True

        controller.processName = "first.exe"
        controller.startProcessTrigger()
        controller.processName = "second.exe"
        controller.startProcessTrigger()

        self.assertEqual(controller.queueTaskCount, 1)
        self.assertNotIn("first.exe", controller.queueText)
        self.assertIn("second.exe", controller.queueText)

    def test_stopping_process_trigger_removes_matching_queue_task(self):
        controller = AppController()
        controller.processName = "demo.exe"
        controller._process_checker = lambda name: True

        controller.startProcessTrigger()
        controller.stopProcessTrigger()

        self.assertFalse(controller.processTriggerActive)
        self.assertNotIn("process_exit", controller.queueRowsJson)
        self.assertEqual(controller.queueTaskCount, 0)

    def test_deleting_active_process_queue_task_stops_process_monitor(self):
        controller = AppController()
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
        controller = AppController(network_reader=FakeNetworkReader(samples))

        controller.networkIdleSeconds = 60
        controller.startNetworkTrigger()
        controller.networkIdleSeconds = 120
        controller.startNetworkTrigger()

        self.assertEqual(controller.queueTaskCount, 1)
        self.assertIn("网络闲置 120 秒", controller.queueText)

    def test_stopping_network_trigger_removes_matching_queue_task(self):
        samples = [NetworkSample(True, received_bytes=1, sent_bytes=1, monotonic_seconds=1.0)]
        controller = AppController(network_reader=FakeNetworkReader(samples))

        controller.startNetworkTrigger()
        controller.stopNetworkTrigger()

        self.assertFalse(controller.networkTriggerActive)
        self.assertNotIn("network_idle", controller.queueRowsJson)
        self.assertEqual(controller.queueTaskCount, 0)

    def test_deleting_active_network_queue_task_stops_network_monitor(self):
        samples = [NetworkSample(True, received_bytes=1, sent_bytes=1, monotonic_seconds=1.0)]
        controller = AppController(network_reader=FakeNetworkReader(samples))
        controller.startNetworkTrigger()
        task_id = controller._scheduler.tasks[0].id

        controller.deleteQueueTask(task_id)

        self.assertFalse(controller.networkTriggerActive)
        self.assertEqual(controller.networkTriggerStatus, "已停止")
        self.assertEqual(controller.queueTaskCount, 0)

    def test_controller_saves_settings_when_persisted_properties_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
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
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
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
        self.assertIn("reset", speed.message)

    def test_network_idle_trigger_fires_after_sustained_low_speed(self):
        samples = [
            NetworkSample(True, received_bytes=1000, sent_bytes=1000, monotonic_seconds=1.0),
            NetworkSample(True, received_bytes=1100, sent_bytes=1100, monotonic_seconds=2.0),
            NetworkSample(True, received_bytes=1200, sent_bytes=1200, monotonic_seconds=3.0),
        ]
        controller = AppController(network_reader=FakeNetworkReader(samples))
        controller.networkDownloadThresholdKbps = 1.0
        controller.networkUploadThresholdKbps = 1.0
        controller.networkIdleSeconds = 2
        controller.networkPollSeconds = 1

        controller.startNetworkTrigger()
        controller._poll_network_trigger()
        controller._poll_network_trigger()

        self.assertFalse(controller.networkTriggerActive)
        self.assertIn("网络闲置触发", controller.logText)
        self.assertIn("[dryRun] Would execute", controller.logText)

    def test_network_busy_sample_resets_idle_accumulation(self):
        samples = [
            NetworkSample(True, received_bytes=0, sent_bytes=0, monotonic_seconds=1.0),
            NetworkSample(True, received_bytes=100, sent_bytes=100, monotonic_seconds=2.0),
            NetworkSample(True, received_bytes=10_000, sent_bytes=100, monotonic_seconds=3.0),
        ]
        controller = AppController(network_reader=FakeNetworkReader(samples))
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
        ]))

        controller.startNetworkTrigger()

        self.assertFalse(controller.networkTriggerActive)
        self.assertIn("network unavailable", controller.networkTriggerStatus)
        self.assertNotIn("[dryRun] Would execute", controller.logText)

    def test_clear_and_export_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            controller = AppController(log_export_path=Path(tmp) / "logs.txt")
            controller.applyTaskTemplate("shutdown_15")

            controller.exportLogs()
            exported = Path(tmp) / "logs.txt"
            self.assertTrue(exported.exists())
            self.assertIn("15 分钟后关机", exported.read_text(encoding="utf-8"))

            controller.clearLogs()
            self.assertNotIn("15 分钟后关机", controller.logText)
            self.assertIn("日志已清空", controller.logText)

    def test_script_path_validation_and_open_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "demo.bat"
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
        with tempfile.TemporaryDirectory() as tmp:
            controller = AppController()
            missing_script = Path(tmp) / "missing-before-shutdown.bat"
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
        with tempfile.TemporaryDirectory() as tmp:
            controller = AppController()
            missing_script = Path(tmp) / "missing-test-script.bat"
            controller.dryRun = False
            controller.scriptEnabled = True
            controller.scriptPath = str(missing_script)
            controller._script_runner = lambda path, timeout: self.fail("script runner should not be called")

            controller.testScript()

            self.assertIn("脚本路径不存在", controller.logText)

    def test_live_script_runner_receives_normalized_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "before-shutdown.bat"
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
        controller = AppController()
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
        controller = AppController()
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
        controller = AppController()
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

    def test_process_trigger_keeps_original_process_name_while_active(self):
        controller = AppController()
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

    def test_diagnostic_text_includes_key_runtime_state(self):
        controller = AppController()
        controller.selectedAction = "sleep"
        controller.scriptEnabled = True
        controller.scriptPath = "C:/demo.bat"

        diagnostics = controller.diagnosticText

        self.assertIn("AutoShutdownQt 2.0", diagnostics)
        self.assertIn("Dry-run: True", diagnostics)
        self.assertIn("Action: sleep", diagnostics)
        self.assertIn("Script enabled: True", diagnostics)
        self.assertIn("Process trigger", diagnostics)
        self.assertIn("Network trigger", diagnostics)

    def test_export_logs_includes_diagnostics_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "logs.txt"
            controller = AppController(log_export_path=target)
            controller.applyTaskTemplate("shutdown_15")

            controller.exportLogs()
            exported = target.read_text(encoding="utf-8")

            self.assertIn("=== Diagnostics ===", exported)
            self.assertIn("AutoShutdownQt 2.0", exported)
            self.assertIn("=== Recent Logs ===", exported)
            self.assertIn("15 分钟后关机", exported)

    def test_export_diagnostics_writes_neighbor_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_target = Path(tmp) / "logs.txt"
            controller = AppController(log_export_path=log_target)

            controller.exportDiagnostics()
            diagnostics_target = Path(tmp) / "logs-diagnostics.txt"

            self.assertTrue(diagnostics_target.exists())
            self.assertIn("AutoShutdownQt 2.0", diagnostics_target.read_text(encoding="utf-8"))
            self.assertIn("诊断已导出", controller.logText)

    def test_request_dry_run_change_logs_live_mode_warning(self):
        controller = AppController()

        controller.requestDryRunChange(False)

        self.assertFalse(controller.dryRun)
        self.assertIn("真实执行模式已开启", controller.logText)
        self.assertIn("请确认", controller.logText)

        controller.requestDryRunChange(True)

        self.assertTrue(controller.dryRun)
        self.assertIn("Dry-run 已开启", controller.logText)

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
