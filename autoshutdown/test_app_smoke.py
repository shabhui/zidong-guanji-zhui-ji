"""界面冒烟测试：真建窗口走一遍状态机，关机调用换成假的。"""

import unittest

try:
    import tkinter as tk

    _root = tk.Tk()
    _root.destroy()
    HAS_DISPLAY = True
except Exception:
    HAS_DISPLAY = False


@unittest.skipUnless(HAS_DISPLAY, "无图形环境")
class AppSmokeTests(unittest.TestCase):
    def setUp(self):
        import app

        self.app_module = app
        self.scheduled = []
        self.cancelled = []
        app.schedule_shutdown = lambda seconds: (self.scheduled.append(seconds), (True, ""))[1]
        app.cancel_shutdown = lambda: (self.cancelled.append(True), (True, ""))[1]

        self.root = tk.Tk()
        self.root.withdraw()
        self.ui = app.ShutdownApp(self.root)
        self.root.update()

    def tearDown(self):
        if self.ui._tick_job is not None:
            self.root.after_cancel(self.ui._tick_job)
        self.root.destroy()

    def test_builds_with_default_countdown_of_one_hour_thirty(self):
        self.assertEqual(self.ui.left.var.get(), "01")
        self.assertEqual(self.ui.right.var.get(), "30")
        self.assertIn("关机", self.ui.status.cget("text"))

    def test_preset_fills_hours_and_minutes(self):
        self.ui._apply_preset(120)
        self.root.update()
        self.assertEqual((self.ui.left.var.get(), self.ui.right.var.get()), ("02", "00"))

    def test_wheel_step_updates_digits(self):
        self.ui._step(self.ui.right, 1)
        self.assertEqual(self.ui.right.var.get(), "31")

    def test_switching_to_absolute_mode_relabels_units(self):
        self.ui.switch.select(1)
        self.ui._on_mode_change(1)
        self.root.update()
        self.assertEqual(self.ui.unit_left.cget("text"), "时")

    def test_arm_schedules_shutdown_and_flips_button_to_cancel(self):
        self.ui._on_action()
        self.root.update()
        self.assertEqual(len(self.scheduled), 1)
        self.assertAlmostEqual(self.scheduled[0], 90 * 60, delta=5)
        self.assertIsNotNone(self.ui.target)

    def test_cancel_clears_target_and_calls_abort(self):
        self.ui._on_action()
        self.root.update()
        self.ui._on_action()
        self.root.update()
        self.assertEqual(len(self.cancelled), 1)
        self.assertIsNone(self.ui.target)
        self.assertEqual(self.ui.left.cget("state"), "normal")

    def test_zero_duration_reports_error_without_scheduling(self):
        self.ui.left.var.set("00")
        self.ui.right.var.set("00")
        self.ui._on_action()
        self.root.update()
        self.assertEqual(self.scheduled, [])
        self.assertIn("至少", self.ui.status.cget("text"))


if __name__ == "__main__":
    unittest.main()
