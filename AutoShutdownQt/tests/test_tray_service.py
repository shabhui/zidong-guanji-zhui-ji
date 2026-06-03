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
        self.assertIn("tray unavailable", messages[0])


if __name__ == "__main__":
    unittest.main()
