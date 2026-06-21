import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
sys.path.insert(0, str(APP_DIR))

from notification_service import NotificationService


class FakeTray:
    def __init__(self):
        self.messages = []

    def showMessage(self, title, body, icon=None, millisecondsTimeoutHint=0):
        self.messages.append((title, body, millisecondsTimeoutHint))


class StrictPySideTray:
    def __init__(self):
        self.messages = []

    def showMessage(self, *args, **kwargs):
        if len(args) >= 3 and args[2] is None:
            raise TypeError("wrong argument types: NoneType")
        self.messages.append((args, kwargs))


class NotificationServiceTest(unittest.TestCase):
    def test_show_reminder_returns_false_without_available_tray(self):
        logs = []
        service = NotificationService(tray_service=None, logger=logs.append)

        self.assertFalse(service.show_reminder("Title", "Body"))
        self.assertIn("系统通知不可用", logs[0])
        self.assertNotIn("notification unavailable", logs[0])

    def test_unavailable_tray_logs_only_once_per_session(self):
        logs = []
        service = NotificationService(tray_service=None, logger=logs.append)

        self.assertFalse(service.show_reminder("Title", "Body"))
        self.assertFalse(service.show_reminder("Title", "Body"))

        self.assertEqual(len(logs), 1)

    def test_show_reminder_logs_chinese_message_when_tray_raises(self):
        class BrokenTray:
            def showMessage(self, title, body, icon=None, millisecondsTimeoutHint=0):
                raise RuntimeError("tray boom")

        logs = []
        tray_service = type("TrayService", (), {"available": True, "tray": BrokenTray()})()
        service = NotificationService(tray_service=tray_service, logger=logs.append)

        self.assertFalse(service.show_reminder("执行前提醒", "1 分钟后关机"))

        self.assertIn("系统通知不可用", logs[0])
        self.assertIn("tray boom", logs[0])
        self.assertNotIn("notification unavailable", logs[0])

    def test_show_reminder_delegates_to_tray_message(self):
        tray = FakeTray()
        tray_service = type("TrayService", (), {"available": True, "tray": tray})()
        service = NotificationService(tray_service=tray_service)

        self.assertTrue(service.show_reminder("执行前提醒", "1 分钟后关机"))

        self.assertEqual(tray.messages, [("执行前提醒", "1 分钟后关机", 10000)])

    def test_show_reminder_uses_valid_qt_tray_icon_argument(self):
        logs = []
        tray = StrictPySideTray()
        tray_service = type("TrayService", (), {"available": True, "tray": tray})()
        service = NotificationService(tray_service=tray_service, logger=logs.append)

        self.assertTrue(service.show_reminder("执行前提醒", "1 分钟后关机"))

        self.assertEqual(logs, [])
        args, kwargs = tray.messages[0]
        self.assertEqual(args[:2], ("执行前提醒", "1 分钟后关机"))
        self.assertNotEqual(args[2], None)
        self.assertIn(10000, args[2:])
        self.assertEqual(kwargs, {})


if __name__ == "__main__":
    unittest.main()
