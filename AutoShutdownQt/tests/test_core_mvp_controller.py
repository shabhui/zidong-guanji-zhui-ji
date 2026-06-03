import sys
from pathlib import Path
import tempfile
import unittest

from PySide6.QtCore import QCoreApplication

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
sys.path.insert(0, str(APP_DIR))

from controller import AppController


class CoreMvpControllerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.controller = AppController()

    def test_task_template_starts_shutdown_countdown_and_logs_it(self):
        self.controller.applyTaskTemplate("shutdown_15")

        self.assertEqual(self.controller.selectedAction, "shutdown")
        self.assertEqual(self.controller.queueTaskCount, 1)
        self.assertIn("倒计时 15 分钟", self.controller.queueText)
        self.assertIn("15 分钟后关机", self.controller.logText)

    def test_fixed_time_template_sets_target_and_logs_it(self):
        self.controller.applyTaskTemplate("shutdown_2300")

        self.assertEqual(self.controller.selectedAction, "shutdown")
        self.assertEqual(self.controller.queueTaskCount, 1)
        self.assertIn("23:00", self.controller.queueText)
        self.assertIn("今晚 23:00 关机", self.controller.logText)

    def test_script_dry_run_does_not_call_script_runner(self):
        calls = []
        self.controller._script_runner = lambda path, timeout: calls.append((path, timeout))
        self.controller.scriptEnabled = True
        self.controller.scriptPath = "C:/tmp/before-shutdown.bat"
        self.controller.scriptTimeoutSeconds = 7

        self.controller.testScript()
        self.controller.executeNow()

        self.assertEqual(calls, [])
        self.assertIn("Dry-run：将执行脚本", self.controller.logText)
        self.assertIn("[dryRun] Would execute", self.controller.logText)

    def test_live_script_failure_blocks_power_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "fail.bat"
            script.write_text("exit /b 1", encoding="utf-8")
            calls = []
            self.controller.dryRun = False
            self.controller.scriptEnabled = True
            self.controller.scriptPath = str(script)
            self.controller._script_runner = lambda path, timeout: type("Result", (), {
                "ok": False,
                "message": "脚本失败：exit 1",
                "stdout": "",
                "stderr": "boom",
                "returncode": 1,
            })()
            self.controller._power_executor = lambda action, force: calls.append((action, force))

            self.controller.executeNow()

            self.assertEqual(calls, [])
            self.assertIn("脚本失败", self.controller.logText)
            self.assertIn("已阻止电源动作", self.controller.logText)

    def test_process_trigger_arms_waiting_for_process_and_can_stop(self):
        self.controller.processName = "definitely-not-running.exe"
        self.controller.processPollSeconds = 2
        self.controller._process_checker = lambda name: False

        self.controller.startProcessTrigger()

        self.assertTrue(self.controller.processTriggerActive)
        self.assertIn("等待进程出现", self.controller.processTriggerStatus)
        self.assertIn("definitely-not-running.exe", self.controller.logText)

        self.controller.stopProcessTrigger()

        self.assertFalse(self.controller.processTriggerActive)
        self.assertIn("已停止", self.controller.processTriggerStatus)

    def test_process_trigger_executes_when_seen_process_exits(self):
        calls = []
        states = [True, False]
        self.controller.processName = "demo.exe"
        self.controller._process_checker = lambda name: states.pop(0)
        self.controller._power_executor = lambda action, force: calls.append((action, force))

        self.controller.startProcessTrigger()
        self.controller._poll_process_trigger()

        self.assertFalse(self.controller.processTriggerActive)
        self.assertEqual(calls, [])
        self.assertIn("进程已退出", self.controller.logText)
        self.assertIn("[dryRun] Would execute", self.controller.logText)


if __name__ == "__main__":
    unittest.main()
