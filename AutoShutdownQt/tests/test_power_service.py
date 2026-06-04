import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
sys.path.insert(0, str(APP_DIR))

import power_service


class PowerServiceTest(unittest.TestCase):
    def test_shutdown_uses_shutdown_exe_with_zero_timeout(self):
        calls = []

        class Completed:
            returncode = 0

        original_run = power_service.subprocess.run
        try:
            power_service.subprocess.run = lambda args, check=False: calls.append((args, check)) or Completed()

            self.assertTrue(power_service.execute_power_action("shutdown", False))
        finally:
            power_service.subprocess.run = original_run

        self.assertEqual(calls, [(["shutdown.exe", "/s", "/t", "0"], False)])

    def test_force_restart_adds_force_flag(self):
        calls = []

        class Completed:
            returncode = 0

        original_run = power_service.subprocess.run
        try:
            power_service.subprocess.run = lambda args, check=False: calls.append((args, check)) or Completed()

            self.assertTrue(power_service.execute_power_action("restart", True))
        finally:
            power_service.subprocess.run = original_run

        self.assertEqual(calls, [(["shutdown.exe", "/r", "/t", "0", "/f"], False)])

    def test_shutdown_command_failure_returns_false(self):
        class Completed:
            returncode = 1

        original_run = power_service.subprocess.run
        try:
            power_service.subprocess.run = lambda args, check=False: Completed()

            self.assertFalse(power_service.execute_power_action("shutdown", False))
        finally:
            power_service.subprocess.run = original_run


if __name__ == "__main__":
    unittest.main()
