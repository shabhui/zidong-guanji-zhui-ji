import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
sys.path.insert(0, str(APP_DIR))

from idle_service import IdleSample, StaticIdleReader, format_idle_status


class IdleServiceTest(unittest.TestCase):
    def test_static_idle_reader_returns_configured_idle_seconds(self):
        reader = StaticIdleReader(125)

        sample = reader.sample()

        self.assertEqual(sample, IdleSample(True, 125, ""))

    def test_format_idle_status_shows_progress_toward_threshold(self):
        self.assertEqual(format_idle_status(120, 300), "已空闲 2 / 5 分钟")
        self.assertEqual(format_idle_status(301, 300), "已空闲 5 / 5 分钟")

    def test_format_idle_status_reports_unavailable_reader(self):
        self.assertEqual(format_idle_status(None, 300, "idle unavailable"), "空闲检测不可用：idle unavailable")


if __name__ == "__main__":
    unittest.main()
