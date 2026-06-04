import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "定时关机助手"
sys.path.insert(0, str(APP_DIR))

from startup_service import StartupService, startup_command


class FakeRegistry:
    def __init__(self):
        self.values = {}
        self.deleted = []

    def set_value(self, name, value):
        self.values[name] = value

    def get_value(self, name):
        return self.values.get(name)

    def delete_value(self, name):
        self.deleted.append(name)
        self.values.pop(name, None)


class StartupServiceTest(unittest.TestCase):
    def test_startup_command_quotes_executable_path(self):
        command = startup_command(Path("C:/Program Files/定时关机助手/定时关机助手.exe"))

        self.assertEqual(command, '"C:/Program Files/定时关机助手/定时关机助手.exe"')

    def test_service_registers_and_unregisters_current_user_run_value(self):
        registry = FakeRegistry()
        service = StartupService(registry=registry, executable=Path("C:/定时关机助手/定时关机助手.exe"))

        self.assertTrue(service.set_enabled(True))
        self.assertEqual(registry.values["定时关机助手"], '"C:/定时关机助手/定时关机助手.exe"')

        self.assertTrue(service.set_enabled(False))
        self.assertIn("定时关机助手", registry.deleted)
        self.assertNotIn("定时关机助手", registry.values)

    def test_service_reports_enabled_only_when_command_matches_current_executable(self):
        registry = FakeRegistry()
        service = StartupService(registry=registry, executable=Path("C:/定时关机助手/定时关机助手.exe"))

        self.assertFalse(service.is_enabled())
        registry.values["定时关机助手"] = '"C:/Other/定时关机助手.exe"'
        self.assertFalse(service.is_enabled())
        registry.values["定时关机助手"] = '"C:/定时关机助手/定时关机助手.exe"'
        self.assertTrue(service.is_enabled())


if __name__ == "__main__":
    unittest.main()
