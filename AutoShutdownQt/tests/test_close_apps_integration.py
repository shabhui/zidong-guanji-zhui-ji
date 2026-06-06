import sys
from pathlib import Path
import unittest

from PySide6.QtCore import QCoreApplication

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
sys.path.insert(0, str(APP_DIR))

from controller import AppController
from app_close_service import AppWindow, StaticAppCloser


def _windows(*specs):
    return [AppWindow(hwnd=hwnd, pid=pid, title=title) for hwnd, pid, title in specs]


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
        self.assertEqual(power_calls, [("shutdown", False)])
        self.assertIn("优雅关闭应用：", self.controller.logText)

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
