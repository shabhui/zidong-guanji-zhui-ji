import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
sys.path.insert(0, str(APP_DIR))

from power_action_context import PowerActionContext


class PowerActionContextTest(unittest.TestCase):
    def test_context_keeps_action_force_and_completion_snapshot(self):
        completion_calls = []

        def completion(success, error):
            completion_calls.append((success, error))

        context = PowerActionContext(
            reason="Retry queue task: nightly",
            action="restart",
            force_close=True,
            close_apps_timeout_seconds=7,
            completion=completion,
            source="queue-retry",
            task_id="task-1",
        )

        self.assertEqual(context.reason, "Retry queue task: nightly")
        self.assertEqual(context.action, "restart")
        self.assertTrue(context.force_close)
        self.assertEqual(context.close_apps_timeout_seconds, 7)
        self.assertEqual(context.source, "queue-retry")
        self.assertEqual(context.task_id, "task-1")

        context.completion(True, "")
        self.assertEqual(completion_calls, [(True, "")])


if __name__ == "__main__":
    unittest.main()
