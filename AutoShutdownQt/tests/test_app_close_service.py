import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
sys.path.insert(0, str(APP_DIR))

from app_close_service import AppWindow, StaticAppCloser, close_user_apps


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


class CloseUserAppsTest(unittest.TestCase):
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
        self.assertIn("仍有 1 个未在", result.message)

    def test_none_closer_is_reported_unavailable(self):
        result = close_user_apps(None)

        self.assertFalse(result.available)
        self.assertIn("不可用", result.message)


if __name__ == "__main__":
    unittest.main()
