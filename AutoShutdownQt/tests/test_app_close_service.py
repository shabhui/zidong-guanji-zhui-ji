import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
sys.path.insert(0, str(APP_DIR))

from app_close_service import AppWindow, CloseAppsResult, StaticAppCloser, close_user_apps, should_ignore_window_class


class FakeClock:
    """Deterministic monotonic clock for timeout tests."""

    def __init__(self):
        self.value = 0.0

    def time(self):
        return self.value

    def sleep(self, seconds):
        self.value += seconds


def _windows(*specs):
    return [AppWindow(hwnd=hwnd, pid=pid, title=title) for hwnd, pid, title in specs]


class FlakyRequestCloser:
    def __init__(self, windows):
        self._live = list(windows)
        self.close_calls = []

    def list_app_windows(self):
        return list(self._live)

    def request_close(self, window):
        self.close_calls.append(window)
        if window.pid == 61:
            raise RuntimeError("window disappeared")
        self._live = [w for w in self._live if w.hwnd != window.hwnd]
        return True


class FailingEnumerationCloser:
    def list_app_windows(self):
        raise RuntimeError("enum unavailable")

    def request_close(self, window):
        raise AssertionError("request_close should not run after enumeration failure")


class CloseUserAppsTest(unittest.TestCase):
    def test_system_window_classes_are_ignored(self):
        ignored = (
            "Progman",
            "WorkerW",
            "Shell_TrayWnd",
            "NotifyIconOverflowWindow",
            "CiceroUIWndFrame",
            "MSCTFIME UI",
        )

        for class_name in ignored:
            with self.subTest(class_name=class_name):
                self.assertTrue(should_ignore_window_class(class_name))

    def test_normal_application_window_classes_are_not_ignored(self):
        for class_name in ("Notepad", "Chrome_WidgetWin_1", "Qt5152QWindowIcon"):
            with self.subTest(class_name=class_name):
                self.assertFalse(should_ignore_window_class(class_name))

    def test_close_apps_result_keeps_legacy_positional_fields(self):
        result = CloseAppsResult(True, 2, 1, 1, ["app"], "message")

        self.assertEqual(result.titles, ["app"])
        self.assertEqual(result.message, "message")
        self.assertFalse(result.cancelled)
        self.assertEqual(result.requested_titles, [])
        self.assertEqual(result.request_failed_titles, [])

    def test_no_windows_reports_nothing_to_close(self):
        closer = StaticAppCloser([])

        result = close_user_apps(closer)

        self.assertTrue(result.available)
        self.assertEqual(result.attempted, 0)
        self.assertEqual(result.closed, 0)
        self.assertEqual(result.remaining, 0)
        self.assertEqual(closer.close_calls, [])
        self.assertIn("没有需要关闭的应用", result.message)

    def test_closes_all_windows_gracefully(self):
        closer = StaticAppCloser(_windows(
            (101, 11, "记事本"),
            (102, 12, "浏览器"),
        ))

        result = close_user_apps(closer, timeout_seconds=5)

        self.assertTrue(result.available)
        self.assertEqual(result.attempted, 2)
        self.assertEqual(result.closed, 2)
        self.assertEqual(result.remaining, 0)
        self.assertEqual({w.title for w in closer.close_calls}, {"记事本", "浏览器"})
        self.assertEqual(result.titles, ["记事本", "浏览器"])
        self.assertEqual(result.requested_titles, ["记事本", "浏览器"])
        self.assertIn("全部已退出", result.message)

    def test_stubborn_app_still_running_after_timeout(self):
        closer = StaticAppCloser(_windows(
            (201, 21, "可关闭"),
            (202, 22, "顽固应用"),
        ), stubborn_pids={22})
        clock = FakeClock()

        result = close_user_apps(
            closer,
            timeout_seconds=2,
            poll_interval=0.5,
            sleep_func=clock.sleep,
            time_func=clock.time,
        )

        # Both were asked to close; only the cooperative one actually exited.
        self.assertEqual(result.attempted, 1)
        self.assertEqual(result.remaining, 1)
        self.assertEqual(result.closed, 1)
        self.assertEqual(result.request_failed_titles, ["顽固应用"])
        self.assertEqual(result.remaining_titles, ["顽固应用"])
        self.assertIn("仍有 1 个未在", result.message)

    def test_cancelled_wait_stops_before_timeout(self):
        closer = StaticAppCloser(_windows((301, 31, "顽固应用")), stubborn_pids={31})
        clock = FakeClock()

        result = close_user_apps(
            closer,
            timeout_seconds=20,
            poll_interval=0.5,
            sleep_func=clock.sleep,
            time_func=clock.time,
            should_stop=lambda: True,
        )

        self.assertEqual(clock.value, 0.0)
        self.assertEqual(result.remaining, 1)
        self.assertTrue(result.cancelled)
        self.assertIn("已跳过等待", result.message)

    def test_poll_sleep_does_not_overshoot_deadline(self):
        closer = StaticAppCloser(_windows((401, 41, "顽固应用")), stubborn_pids={41})
        clock = FakeClock()

        result = close_user_apps(
            closer,
            timeout_seconds=1,
            poll_interval=0.75,
            sleep_func=clock.sleep,
            time_func=clock.time,
        )

        self.assertEqual(clock.value, 1.0)
        self.assertEqual(result.remaining, 1)

    def test_invalid_timeout_falls_back_to_immediate_poll(self):
        closer = StaticAppCloser(_windows((501, 51, "顽固应用")), stubborn_pids={51})
        clock = FakeClock()

        result = close_user_apps(
            closer,
            timeout_seconds="bad-value",
            poll_interval="bad-value",
            sleep_func=clock.sleep,
            time_func=clock.time,
        )

        self.assertEqual(clock.value, 0.0)
        self.assertEqual(result.remaining, 1)

    def test_request_close_exception_does_not_stop_other_windows(self):
        closer = FlakyRequestCloser(_windows(
            (601, 61, "消失的窗口"),
            (602, 62, "正常窗口"),
        ))

        result = close_user_apps(closer, timeout_seconds=0)

        self.assertEqual([w.pid for w in closer.close_calls], [61, 62])
        self.assertEqual(result.attempted, 1)

    def test_none_closer_is_reported_unavailable(self):
        result = close_user_apps(None)

        self.assertFalse(result.available)
        self.assertIn("不可用", result.message)

    def test_enumeration_failure_is_reported_unavailable(self):
        result = close_user_apps(FailingEnumerationCloser())

        self.assertFalse(result.available)
        self.assertEqual(result.attempted, 0)
        self.assertIn("enum unavailable", result.message)


if __name__ == "__main__":
    unittest.main()
