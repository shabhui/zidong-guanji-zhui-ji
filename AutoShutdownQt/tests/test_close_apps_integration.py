import sys
import json
import time
from pathlib import Path
import threading
import unittest

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
sys.path.insert(0, str(APP_DIR))

from tests.qt_test_env import ensure_qt_modules
ensure_qt_modules()

from PySide6.QtCore import QCoreApplication

from controller import AppController
from app_close_service import AppWindow, StaticAppCloser


def _windows(*specs):
    return [AppWindow(hwnd=hwnd, pid=pid, title=title) for hwnd, pid, title in specs]


def _wait_for_calls(calls, expected, timeout=2):
    deadline = time.monotonic() + timeout
    while calls != expected and time.monotonic() < deadline:
        QCoreApplication.processEvents()
        time.sleep(0.02)
    QCoreApplication.processEvents()
    return calls


def _wait_for_queue_status(controller, expected_status, timeout=2):
    deadline = time.monotonic() + timeout
    while expected_status not in _queue_statuses(controller) and time.monotonic() < deadline:
        QCoreApplication.processEvents()
        time.sleep(0.02)
    QCoreApplication.processEvents()
    return _queue_statuses(controller)


def _queue_statuses(controller):
    return [row["status"] for row in json.loads(controller.queueRowsJson)]


class AlwaysStubbornCloser:
    def __init__(self, windows):
        self._windows = list(windows)
        self.close_calls = []

    def list_app_windows(self):
        return list(self._windows)

    def request_close(self, window):
        self.close_calls.append(window)
        return True


class FailingListCloser:
    close_calls = []

    def list_app_windows(self):
        raise RuntimeError("enum boom")

    def request_close(self, window):
        self.close_calls.append(window)
        return True


class CloseAppsIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.controller = AppController()

    def test_dry_run_only_lists_apps_without_closing(self):
        closer = StaticAppCloser(_windows((1, 10, "记事本"), (2, 11, "浏览器")))
        self.controller._app_closer = closer
        self.controller.closeAppsBeforeAction = True

        self.controller.executeNow()

        self.assertEqual(closer.close_calls, [])  # nothing closed in dry-run
        self.assertIn("将优雅关闭 2 个应用", self.controller.logText)
        self.assertIn("[dryRun] Would execute", self.controller.logText)

    def test_preview_close_apps_lists_windows_without_closing(self):
        closer = StaticAppCloser(_windows((1, 10, "记事本"), (2, 11, "浏览器")))
        self.controller._app_closer = closer

        self.controller.previewCloseApps()

        self.assertEqual(closer.close_calls, [])
        self.assertIn("关闭应用预检", self.controller.logText)
        self.assertIn("记事本", self.controller.logText)
        self.assertIn("浏览器", self.controller.logText)

    def test_preview_close_apps_summarizes_long_window_lists(self):
        closer = StaticAppCloser(_windows(*[
            (index, 100 + index, f"应用{index}")
            for index in range(1, 11)
        ]))
        self.controller._app_closer = closer

        self.controller.previewCloseApps()

        self.assertIn("等 2 个", self.controller.logText)
        self.assertNotIn("应用10", self.controller.logText)

    def test_preview_close_apps_reports_enumeration_failure(self):
        self.controller._app_closer = FailingListCloser()

        self.controller.previewCloseApps()

        self.assertIn("关闭应用预检失败", self.controller.logText)
        self.assertIn("enum boom", self.controller.logText)

    def test_close_apps_failure_updates_last_result_diagnostics(self):
        self.controller._app_closer = FailingListCloser()
        self.controller._close_apps_with_closer(self.controller._app_closer, 1)

        self.assertIn("Close apps last result", self.controller.diagnosticText)
        self.assertIn("available=False", self.controller.diagnosticText)
        self.assertIn("enum boom", self.controller.diagnosticText)

    def test_live_closes_apps_then_runs_power_action(self):
        closer = StaticAppCloser(_windows((1, 10, "记事本"), (2, 11, "浏览器")))
        power_calls = []
        self.controller._app_closer = closer
        self.controller._power_executor = lambda action, force: power_calls.append((action, force)) or True
        self.controller.dryRun = False
        self.controller.selectedAction = "shutdown"
        self.controller.closeAppsBeforeAction = True

        self.controller.executeNow()

        self.assertEqual(len(closer.close_calls), 2)
        self.assertEqual(_wait_for_calls(power_calls, [("shutdown", False)]), [("shutdown", False)])
        self.assertIn("优雅关闭应用：", self.controller.logText)
        self.assertIn("已请求关闭：记事本、浏览器", self.controller.logText)
        self.assertIn("Close apps last result", self.controller.diagnosticText)
        self.assertIn("attempted=2", self.controller.diagnosticText)

    def test_live_close_apps_does_not_block_ui_thread(self):
        closer = AlwaysStubbornCloser(_windows((1, 10, "未保存的文档")))
        power_calls = []
        self.controller._app_closer = closer
        self.controller._power_executor = lambda action, force: power_calls.append((action, force)) or True
        self.controller.dryRun = False
        self.controller.selectedAction = "shutdown"
        self.controller.closeAppsBeforeAction = True
        self.controller.closeAppsTimeoutSeconds = 1

        started = time.monotonic()
        self.controller.executeNow()
        elapsed = time.monotonic() - started

        self.assertLess(elapsed, 0.2)
        self.assertEqual(_wait_for_calls(power_calls, [("shutdown", False)]), [("shutdown", False)])

    def test_live_close_apps_ignores_duplicate_trigger_while_pending(self):
        closer = AlwaysStubbornCloser(_windows((1, 10, "未保存的文档")))
        power_calls = []
        self.controller._app_closer = closer
        self.controller._power_executor = lambda action, force: power_calls.append((action, force)) or True
        self.controller.dryRun = False
        self.controller.selectedAction = "shutdown"
        self.controller.closeAppsBeforeAction = True
        self.controller.closeAppsTimeoutSeconds = 1

        self.controller.executeNow()
        self.controller.executeNow()

        self.assertEqual(_wait_for_calls(power_calls, [("shutdown", False)]), [("shutdown", False)])
        self.assertIn("已有电源动作正在执行", self.controller.logText)

    def test_async_queue_task_marks_executed_after_power_action_finishes(self):
        closer = AlwaysStubbornCloser(_windows((1, 10, "未保存的文档")))
        power_calls = []
        self.controller._app_closer = closer
        self.controller._power_executor = lambda action, force: power_calls.append((action, force)) or True
        self.controller.dryRun = False
        self.controller.closeAppsBeforeAction = True
        self.controller.closeAppsTimeoutSeconds = 1
        self.controller.startCountdown(0, 0, 1)
        task = self.controller._scheduler.tasks[0]
        task.next_run_at = self.controller._now()

        self.controller._on_tick()

        self.assertNotIn("completed", _queue_statuses(self.controller))
        self.assertEqual(_wait_for_calls(power_calls, [("shutdown", False)]), [("shutdown", False)])
        self.assertIn("completed", _queue_statuses(self.controller))

    def test_retry_failed_async_queue_task_marks_executed_after_power_action_finishes(self):
        initial_calls = []
        self.controller.dryRun = False
        self.controller.selectedAction = "restart"
        self.controller.forceClose = True
        self.controller._power_executor = lambda action, force: initial_calls.append((action, force)) or False
        self.controller.startCountdown(0, 0, 1)
        task = self.controller._scheduler.tasks[0]
        task.next_run_at = self.controller._now()

        self.controller._on_tick()
        self.assertIn("failed", _queue_statuses(self.controller))
        self.assertEqual(initial_calls, [("restart", True)])

        closer = StaticAppCloser(_windows((1, 10, "retry-app")))
        entered_power_action = threading.Event()
        release_power_action = threading.Event()
        retry_calls = []

        def power_executor(action, force):
            retry_calls.append((action, force))
            entered_power_action.set()
            release_power_action.wait(2)
            return True

        self.controller._app_closer = closer
        self.controller._power_executor = power_executor
        self.controller.selectedAction = "shutdown"
        self.controller.forceClose = False
        self.controller.closeAppsBeforeAction = True

        self.controller.retryQueueTask(task.id)
        self.assertTrue(entered_power_action.wait(1))
        QCoreApplication.processEvents()

        self.assertEqual(retry_calls, [("restart", True)])
        self.assertIn("failed", _queue_statuses(self.controller))
        self.assertNotIn("completed", _queue_statuses(self.controller))

        release_power_action.set()
        self.assertIn("completed", _wait_for_queue_status(self.controller, "completed"))
        self.assertIn("completed", _queue_statuses(self.controller))

    def test_power_action_in_progress_property_toggles_around_async_close(self):
        closer = AlwaysStubbornCloser(_windows((1, 10, "未保存的文档")))
        power_calls = []
        self.controller._app_closer = closer
        self.controller._power_executor = lambda action, force: power_calls.append((action, force)) or True
        self.controller.dryRun = False
        self.controller.selectedAction = "shutdown"
        self.controller.closeAppsBeforeAction = True
        self.controller.closeAppsTimeoutSeconds = 1

        self.controller.executeNow()

        self.assertTrue(self.controller.powerActionInProgress)
        self.assertIn("正在优雅关闭应用", self.controller.powerActionProgressText)
        self.assertEqual(_wait_for_calls(power_calls, [("shutdown", False)]), [("shutdown", False)])
        self.assertFalse(self.controller.powerActionInProgress)
        self.assertEqual("", self.controller.powerActionProgressText)

    def test_progress_text_updates_after_close_apps_wait_finishes(self):
        closer = StaticAppCloser(_windows((1, 10, "记事本")))
        entered_power_action = threading.Event()
        release_power_action = threading.Event()
        power_calls = []

        def power_executor(action, force):
            power_calls.append((action, force))
            entered_power_action.set()
            release_power_action.wait(2)
            return True

        self.controller._app_closer = closer
        self.controller._power_executor = power_executor
        self.controller.dryRun = False
        self.controller.selectedAction = "shutdown"
        self.controller.closeAppsBeforeAction = True

        self.controller.executeNow()
        self.assertTrue(entered_power_action.wait(1))
        QCoreApplication.processEvents()

        self.assertIn("正在执行", self.controller.powerActionProgressText)
        self.assertFalse(self.controller.canSkipCloseAppsWait)

        release_power_action.set()
        self.assertEqual(_wait_for_calls(power_calls, [("shutdown", False)]), [("shutdown", False)])

    def test_close_apps_timeout_seconds_is_capped_to_five_minutes(self):
        self.controller.closeAppsTimeoutSeconds = 999

        self.assertEqual(self.controller.closeAppsTimeoutSeconds, 300)
        self.assertIn("已调整为 300 秒", self.controller.logText)

    def test_close_apps_settings_are_locked_during_power_action(self):
        closer = AlwaysStubbornCloser(_windows((1, 10, "未保存的文档")))
        self.controller._app_closer = closer
        self.controller._power_executor = lambda action, force: True
        self.controller.dryRun = False
        self.controller.selectedAction = "shutdown"
        self.controller.closeAppsBeforeAction = True
        self.controller.closeAppsTimeoutSeconds = 1

        self.controller.executeNow()
        self.assertTrue(self.controller.powerActionInProgress)

        self.controller.closeAppsBeforeAction = False
        self.controller.closeAppsTimeoutSeconds = 5

        self.assertTrue(self.controller.closeAppsBeforeAction)
        self.assertEqual(self.controller.closeAppsTimeoutSeconds, 1)
        self.assertIn("电源动作执行中", self.controller.logText)

    def test_skip_close_apps_wait_executes_power_without_full_timeout(self):
        closer = AlwaysStubbornCloser(_windows((1, 10, "未保存的文档")))
        power_calls = []
        self.controller._app_closer = closer
        self.controller._power_executor = lambda action, force: power_calls.append((action, force)) or True
        self.controller.dryRun = False
        self.controller.selectedAction = "shutdown"
        self.controller.closeAppsBeforeAction = True
        self.controller.closeAppsTimeoutSeconds = 5

        started = time.monotonic()
        self.controller.executeNow()
        self.controller.skipCloseAppsWait()

        self.assertEqual(_wait_for_calls(power_calls, [("shutdown", False)]), [("shutdown", False)])
        self.assertLess(time.monotonic() - started, 1.5)
        self.assertIn("已跳过优雅关闭等待", self.controller.logText)

    def test_non_session_action_skips_closing(self):
        closer = StaticAppCloser(_windows((1, 10, "记事本")))
        power_calls = []
        self.controller._app_closer = closer
        self.controller._power_executor = lambda action, force: power_calls.append((action, force)) or True
        self.controller.dryRun = False
        self.controller.selectedAction = "lock"
        self.controller.closeAppsBeforeAction = True

        self.controller.executeNow()

        self.assertEqual(closer.close_calls, [])  # lock does not end the session
        self.assertEqual(power_calls, [("lock", False)])

    def test_live_close_apps_logs_remaining_window_titles(self):
        closer = StaticAppCloser(_windows(
            (1, 10, "可关闭"),
            (2, 11, "未保存文档"),
        ), stubborn_pids={11})
        power_calls = []
        self.controller._app_closer = closer
        self.controller._power_executor = lambda action, force: power_calls.append((action, force)) or True
        self.controller.dryRun = False
        self.controller.selectedAction = "shutdown"
        self.controller.closeAppsBeforeAction = True
        self.controller.closeAppsTimeoutSeconds = 0

        self.controller.executeNow()

        self.assertEqual(_wait_for_calls(power_calls, [("shutdown", False)]), [("shutdown", False)])
        self.assertIn("仍未退出：未保存文档", self.controller.logText)
        self.assertIn("关闭请求失败：未保存文档", self.controller.logText)
        self.assertIn("requestFailed=1", self.controller.diagnosticText)

    def test_disabled_setting_never_touches_closer(self):
        closer = StaticAppCloser(_windows((1, 10, "记事本")))
        self.controller._app_closer = closer
        self.controller.dryRun = False
        self.controller._power_executor = lambda action, force: True
        self.controller.closeAppsBeforeAction = False

        self.controller.executeNow()

        self.assertEqual(closer.close_calls, [])

    def test_setting_round_trips_through_settings_snapshot(self):
        self.controller.closeAppsBeforeAction = True
        self.controller.closeAppsTimeoutSeconds = 45

        snapshot = self.controller._settings_snapshot()

        self.assertTrue(snapshot["closeAppsBeforeAction"])
        self.assertEqual(snapshot["closeAppsTimeoutSeconds"], 45)


if __name__ == "__main__":
    unittest.main()
