import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
sys.path.insert(0, str(APP_DIR))

from task_model import RepeatRule, ScheduledTask, TaskStatus, TaskTriggerType


class TaskModelTest(unittest.TestCase):
    def test_countdown_task_round_trips_with_defaults_and_summary(self):
        task = ScheduledTask.create(
            name="30 分钟后关机",
            action="shutdown",
            force_close=False,
            trigger_type=TaskTriggerType.COUNTDOWN,
            trigger_config={"seconds": 1800},
            repeat_rule=RepeatRule.ONCE,
            created_order=3,
        )
        task.next_run_at = datetime(2026, 6, 3, 12, 30, tzinfo=timezone.utc)

        restored = ScheduledTask.from_dict(task.to_dict())

        self.assertEqual(restored.name, "30 分钟后关机")
        self.assertEqual(restored.action, "shutdown")
        self.assertEqual(restored.trigger_type, TaskTriggerType.COUNTDOWN)
        self.assertEqual(restored.repeat_rule, RepeatRule.ONCE)
        self.assertEqual(restored.status, TaskStatus.PENDING)
        self.assertTrue(restored.enabled)
        self.assertEqual(restored.created_order, 3)
        self.assertEqual(restored.trigger_summary(), "倒计时 30 分钟")
        self.assertEqual(restored.repeat_summary(), "仅一次")
        self.assertEqual(restored.next_run_text(), "2026-06-03 12:30")

    def test_fixed_time_recurring_summary(self):
        task = ScheduledTask.create(
            name="工作日 23:00 睡眠",
            action="sleep",
            force_close=False,
            trigger_type=TaskTriggerType.FIXED_TIME,
            trigger_config={"hour": 23, "minute": 0},
            repeat_rule=RepeatRule.WEEKDAYS,
            created_order=1,
        )

        self.assertEqual(task.trigger_summary(), "固定时间 23:00")
        self.assertEqual(task.repeat_summary(), "工作日")

    def test_invalid_task_entries_are_rejected(self):
        invalid = {
            "id": "bad",
            "name": "bad",
            "action": "format-disk",
            "triggerType": "countdown",
            "triggerConfig": {"seconds": 60},
            "repeatRule": "once",
            "createdOrder": 1,
        }

        with self.assertRaisesRegex(ValueError, "action"):
            ScheduledTask.from_dict(invalid)

    def test_process_and_network_summaries(self):
        process_task = ScheduledTask.create(
            name="等待 notepad 退出",
            action="shutdown",
            force_close=False,
            trigger_type=TaskTriggerType.PROCESS_EXIT,
            trigger_config={"processName": "notepad.exe", "pollSeconds": 5},
            repeat_rule=RepeatRule.ONCE,
            created_order=1,
        )
        network_task = ScheduledTask.create(
            name="网络闲置后睡眠",
            action="sleep",
            force_close=False,
            trigger_type=TaskTriggerType.NETWORK_IDLE,
            trigger_config={"downloadKbps": 10.0, "uploadKbps": 10.0, "idleSeconds": 60, "pollSeconds": 3},
            repeat_rule=RepeatRule.ONCE,
            created_order=2,
        )

        idle_task = ScheduledTask.create(
            name="空闲触发",
            action="shutdown",
            force_close=False,
            trigger_type=TaskTriggerType.IDLE,
            trigger_config={"idleMinutes": 30, "pollSeconds": 10},
            repeat_rule=RepeatRule.ONCE,
            created_order=3,
        )

        self.assertEqual(process_task.trigger_summary(), "进程退出 notepad.exe")
        self.assertEqual(network_task.trigger_summary(), "网络闲置 60 秒")
        self.assertEqual(idle_task.trigger_summary(), "空闲 30 分钟")


if __name__ == "__main__":
    unittest.main()
