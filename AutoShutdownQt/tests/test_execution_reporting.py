import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
sys.path.insert(0, str(APP_DIR))

from execution_reporting import exception_text


class EmptyMessageError(Exception):
    def __str__(self):
        return ""


class ExecutionReportingTest(unittest.TestCase):
    def test_exception_text_uses_message_when_present(self):
        self.assertEqual(exception_text(RuntimeError("boom")), "boom")

    def test_exception_text_falls_back_to_class_name_for_empty_message(self):
        self.assertEqual(exception_text(EmptyMessageError()), "EmptyMessageError")


if __name__ == "__main__":
    unittest.main()
