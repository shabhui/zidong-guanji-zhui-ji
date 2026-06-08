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
        self.assertEqual(format_idle_status(None, 300, "idle unavailable"), "空闲检测不可用：系统未提供空闲状态")

    def test_format_idle_status_uses_chinese_fallback_for_missing_message(self):
        self.assertEqual(format_idle_status(None, 300, ""), "空闲检测不可用：原因未知")
        self.assertNotIn("unknown", format_idle_status(None, 300, ""))

    def test_format_idle_status_localizes_common_windows_reader_error(self):
        self.assertEqual(
            format_idle_status(None, 300, "GetLastInputInfo failed"),
            "空闲检测不可用：系统未返回最近输入时间",
        )
        self.assertNotIn("GetLastInputInfo", format_idle_status(None, 300, "GetLastInputInfo failed"))


if __name__ == "__main__":
    unittest.main()
