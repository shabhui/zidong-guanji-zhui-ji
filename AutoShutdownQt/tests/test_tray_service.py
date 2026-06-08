import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
sys.path.insert(0, str(APP_DIR))

from tray_service import TrayService


class FakeWindow:
    def __init__(self):
        self.visible = True
        self.show_calls = 0
        self.hide_calls = 0

    def show(self):
        self.visible = True
        self.show_calls += 1

    def hide(self):
        self.visible = False
        self.hide_calls += 1


class FakeSignal:
    def __init__(self):
        self.callback = None

    def connect(self, callback):
        self.callback = callback

    def emit(self, reason):
        self.callback(reason)


class FakeTray:
    DoubleClick = 2

    def __init__(self):
        self.messages = []
        self.activated = FakeSignal()

    def showMessage(self, title, body, icon=None, millisecondsTimeoutHint=0):
        self.messages.append((title, body, icon, millisecondsTimeoutHint))


class FakeController:
    def __init__(self):
        self.paused = False
        self.cancelled = False
        self.quit_requested = False

    @property
    def schedulingPaused(self):
        return self.paused

    def pauseScheduling(self):
        self.paused = True

    def resumeScheduling(self):
        self.paused = False

    def cancelAllTasks(self):
        self.cancelled = True

    def requestQuit(self):
        self.quit_requested = True


class TrayServiceTest(unittest.TestCase):
    def test_show_hide_pause_resume_cancel_and_quit_callbacks(self):
        window = FakeWindow()
        controller = FakeController()
        service = TrayService(controller, window, tray_factory=lambda: None)

        service.hide_window()
        service.show_window()
        service.pause_or_resume()
        service.cancel_all()
        service.quit_app()

        self.assertEqual(window.hide_calls, 1)
        self.assertEqual(window.show_calls, 1)
        self.assertTrue(controller.paused)
        self.assertTrue(controller.cancelled)
        self.assertTrue(controller.quit_requested)

    def test_unavailable_tray_keeps_window_mode_usable(self):
        window = FakeWindow()
        controller = FakeController()
        messages = []

        service = TrayService(controller, window, tray_factory=lambda: None, logger=messages.append)
        available = service.setup()

        self.assertFalse(available)
        self.assertIn("托盘不可用", messages[0])
        self.assertNotIn("tray unavailable", messages[0])

    def test_unavailable_tray_logs_chinese_when_factory_raises(self):
        window = FakeWindow()
        controller = FakeController()
        messages = []
        service = TrayService(
            controller,
            window,
            tray_factory=lambda: (_ for _ in ()).throw(RuntimeError("boom")),
            logger=messages.append,
        )

        available = service.setup()

        self.assertFalse(available)
        self.assertIn("托盘不可用：boom", messages[0])
        self.assertNotIn("tray unavailable", messages[0])

    def test_quit_app_marks_window_for_explicit_quit_when_property_exists(self):
        window = FakeWindow()
        window.trayCloseRequested = False
        controller = FakeController()
        service = TrayService(controller, window, tray_factory=lambda: object())

        service.quit_app()

        self.assertTrue(window.trayCloseRequested)
        self.assertTrue(controller.quit_requested)

    def test_minimize_to_tray_hides_window_and_shows_tray_hint(self):
        window = FakeWindow()
        controller = FakeController()
        tray = FakeTray()
        service = TrayService(controller, window, tray_factory=lambda: tray)
        service.setup()

        minimized = service.minimize_to_tray()

        self.assertTrue(minimized)
        self.assertFalse(window.visible)
        self.assertEqual(window.hide_calls, 1)
        self.assertEqual(len(tray.messages), 1)
        self.assertEqual(tray.messages[0][0], "定时关机助手")
        self.assertIn("小图标", tray.messages[0][1])
        self.assertIn("双击", tray.messages[0][1])
        self.assertIn("右键", tray.messages[0][1])

    def test_minimize_to_tray_keeps_window_visible_when_tray_unavailable(self):
        window = FakeWindow()
        controller = FakeController()
        messages = []
        service = TrayService(controller, window, tray_factory=lambda: None, logger=messages.append)
        service.setup()

        minimized = service.minimize_to_tray()

        self.assertFalse(minimized)
        self.assertTrue(window.visible)
        self.assertEqual(window.hide_calls, 0)
        self.assertIn("最小化到托盘已跳过：托盘不可用", messages[-1])
        self.assertNotIn("minimize to tray", messages[-1])

    def test_double_clicking_tray_icon_shows_hidden_window(self):
        window = FakeWindow()
        controller = FakeController()
        tray = FakeTray()
        service = TrayService(controller, window, tray_factory=lambda: tray)
        service.setup()
        service.minimize_to_tray()

        tray.activated.emit(tray.DoubleClick)

        self.assertTrue(window.visible)
        self.assertEqual(window.show_calls, 1)

    def test_real_tray_uses_explicit_app_icon_path_for_system_tray_icon(self):
        source = (APP_DIR / "tray_service.py").read_text(encoding="utf-8")

        self.assertIn("icon_path=None", source)
        self.assertIn("self._icon_path", source)
        self.assertIn("QIcon(str(self._icon_path))", source)
        self.assertIn("tray.setIcon(icon)", source)

    def test_real_tray_context_menu_uses_chinese_labels(self):
        source = (APP_DIR / "tray_service.py").read_text(encoding="utf-8")

        for label in ("显示/隐藏窗口", "暂停/继续任务", "取消所有任务", "退出程序"):
            self.assertIn(label, source)
        for stale_label in ("Show/Hide", "Pause/Resume scheduling", "Cancel all tasks", 'menu.addAction("Quit"'):
            self.assertNotIn(stale_label, source)


if __name__ == "__main__":
    unittest.main()
