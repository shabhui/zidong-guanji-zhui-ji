import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
sys.path.insert(0, str(APP_DIR))

from task_model import RepeatRule, ScheduledTask, TaskStatus, TaskTriggerType
from task_scheduler import TaskScheduler


class TaskSchedulerTest(unittest.TestCase):
    def test_once_countdown_task_is_removed_after_successful_execution(self):
        now = datetime(2026, 6, 3, 12, 0, 0)
        scheduler = TaskScheduler(now_provider=lambda: now)

        task = scheduler.add_task("10 秒后锁定", "lock", False, TaskTriggerType.COUNTDOWN, {"seconds": 10}, RepeatRule.ONCE)

        self.assertEqual(task.next_run_at, now + timedelta(seconds=10))
        due = scheduler.due_tasks(now + timedelta(seconds=10))
        self.assertEqual([item.id for item in due], [task.id])

        scheduler.mark_executed(task.id, now + timedelta(seconds=10), success=True)

        self.assertEqual(scheduler.tasks, [])
        with self.assertRaises(KeyError):
            scheduler.get_task(task.id)

    def test_fixed_time_daily_reschedules_to_next_valid_day(self):
        now = datetime(2026, 6, 3, 23, 30, 0)
        scheduler = TaskScheduler(now_provider=lambda: now)

        task = scheduler.add_task("每天 23:00 睡眠", "sleep", False, TaskTriggerType.FIXED_TIME, {"hour": 23, "minute": 0}, RepeatRule.DAILY)

        self.assertEqual(task.next_run_at, datetime(2026, 6, 4, 23, 0, 0))
        scheduler.mark_executed(task.id, datetime(2026, 6, 4, 23, 0, 0), success=True)
        self.assertEqual(scheduler.get_task(task.id).next_run_at, datetime(2026, 6, 5, 23, 0, 0))
        self.assertEqual(scheduler.get_task(task.id).status, TaskStatus.PENDING)

    def test_weekday_and_weekend_rules_skip_invalid_days(self):
        friday = datetime(2026, 6, 5, 23, 30, 0)
        scheduler = TaskScheduler(now_provider=lambda: friday)

        weekday = scheduler.add_task("工作日 23:00", "shutdown", False, TaskTriggerType.FIXED_TIME, {"hour": 23, "minute": 0}, RepeatRule.WEEKDAYS)
        weekend = scheduler.add_task("周末 08:00", "shutdown", False, TaskTriggerType.FIXED_TIME, {"hour": 8, "minute": 0}, RepeatRule.WEEKENDS)

        self.assertEqual(weekday.next_run_at, datetime(2026, 6, 8, 23, 0, 0))
        self.assertEqual(weekend.next_run_at, datetime(2026, 6, 6, 8, 0, 0))

    def test_due_tasks_are_ordered_by_time_then_created_order(self):
        now = datetime(2026, 6, 3, 12, 0, 0)
        scheduler = TaskScheduler(now_provider=lambda: now)
        second = scheduler.add_task("second", "sleep", False, TaskTriggerType.COUNTDOWN, {"seconds": 20}, RepeatRule.ONCE)
        first = scheduler.add_task("first", "lock", False, TaskTriggerType.COUNTDOWN, {"seconds": 10}, RepeatRule.ONCE)
        third_same_time = scheduler.add_task("third", "shutdown", False, TaskTriggerType.COUNTDOWN, {"seconds": 20}, RepeatRule.ONCE)

        due = scheduler.due_tasks(now + timedelta(seconds=20))

        self.assertEqual([task.id for task in due], [first.id, second.id, third_same_time.id])

    def test_disable_prevents_due_without_losing_configuration(self):
        now = datetime(2026, 6, 3, 12, 0, 0)
        scheduler = TaskScheduler(now_provider=lambda: now)
        task = scheduler.add_task("disabled", "lock", False, TaskTriggerType.COUNTDOWN, {"seconds": 1}, RepeatRule.ONCE)

        scheduler.set_enabled(task.id, False)

        self.assertEqual(scheduler.due_tasks(now + timedelta(seconds=5)), [])
        self.assertFalse(scheduler.get_task(task.id).enabled)
        self.assertEqual(scheduler.get_task(task.id).trigger_config["seconds"], 1)

    def test_load_preserves_saved_next_run_time(self):
        saved_next_run = datetime(2026, 6, 3, 12, 10, 0)
        scheduler = TaskScheduler(now_provider=lambda: datetime(2026, 6, 3, 12, 0, 0))
        task_data = ScheduledTask.create("saved", "lock", False, TaskTriggerType.COUNTDOWN, {"seconds": 60}, RepeatRule.ONCE, 1).to_dict()
        task_data["nextRunAt"] = saved_next_run.isoformat()

        scheduler.load_from_settings({"version": 1, "tasks": [task_data]})

        self.assertEqual(scheduler.tasks[0].next_run_at, saved_next_run)

    def test_disable_marks_task_paused_without_losing_configuration(self):
        now = datetime(2026, 6, 3, 12, 0, 0)
        scheduler = TaskScheduler(now_provider=lambda: now)
        task = scheduler.add_task("disabled", "lock", False, TaskTriggerType.COUNTDOWN, {"seconds": 1}, RepeatRule.ONCE)

        scheduler.set_enabled(task.id, False)

        self.assertEqual(scheduler.due_tasks(now + timedelta(seconds=5)), [])
        self.assertFalse(scheduler.get_task(task.id).enabled)
        self.assertEqual(scheduler.get_task(task.id).status, TaskStatus.PAUSED)
        self.assertIsNone(scheduler.get_task(task.id).next_run_at)
        self.assertEqual(scheduler.get_task(task.id).trigger_config["seconds"], 1)

    def test_reenable_paused_task_reschedules_it(self):
        now = datetime(2026, 6, 3, 12, 0, 0)
        scheduler = TaskScheduler(now_provider=lambda: now)
        task = scheduler.add_task("disabled", "lock", False, TaskTriggerType.COUNTDOWN, {"seconds": 1}, RepeatRule.ONCE)
        scheduler.set_enabled(task.id, False)

        scheduler.set_enabled(task.id, True)

        self.assertEqual(scheduler.get_task(task.id).status, TaskStatus.PENDING)
        self.assertEqual(scheduler.get_task(task.id).next_run_at, now + timedelta(seconds=1))

    def test_rows_include_localized_status_label_for_ui(self):
        now = datetime(2026, 6, 3, 12, 0, 0)
        scheduler = TaskScheduler(now_provider=lambda: now)
        task = scheduler.add_task("10 秒后锁定", "lock", False, TaskTriggerType.COUNTDOWN, {"seconds": 10}, RepeatRule.ONCE)

        pending_row = scheduler.rows()[0]
        scheduler.set_enabled(task.id, False)
        paused_row = scheduler.rows()[0]
        scheduler.set_enabled(task.id, True)
        scheduler.mark_executed(task.id, now + timedelta(seconds=10), success=False, error="power rejected")
        failed_row = scheduler.rows()[0]

        self.assertEqual(pending_row["status"], "pending")
        self.assertEqual(pending_row["statusLabel"], "待执行")
        self.assertEqual(paused_row["statusLabel"], "已暂停")
        self.assertEqual(failed_row["status"], "failed")
        self.assertEqual(failed_row["statusLabel"], "失败")

    def test_failed_task_without_error_uses_localized_fallback_for_ui(self):
        now = datetime(2026, 6, 3, 12, 0, 0)
        scheduler = TaskScheduler(now_provider=lambda: now)
        task = scheduler.add_task("fallback", "lock", False, TaskTriggerType.COUNTDOWN, {"seconds": 1}, RepeatRule.ONCE)

        scheduler.mark_executed(task.id, now + timedelta(seconds=1), success=False, error="")

        row = scheduler.rows()[0]
        self.assertEqual(row["lastError"], "执行失败")
        self.assertNotIn("execution failed", row["lastError"])

    def test_load_prunes_completed_once_tasks(self):
        task_data = ScheduledTask.create("done", "lock", False, TaskTriggerType.COUNTDOWN, {"seconds": 60}, RepeatRule.ONCE, 1).to_dict()
        task_data["status"] = TaskStatus.COMPLETED.value
        task_data["nextRunAt"] = datetime(2026, 6, 3, 12, 10, 0).isoformat()
        scheduler = TaskScheduler()

        scheduler.load_from_settings({"version": 1, "tasks": [task_data]})

        self.assertEqual(scheduler.tasks, [])

    def test_load_ignores_invalid_entries_with_diagnostics(self):
        diagnostics = []
        scheduler = TaskScheduler(diagnostic_logger=diagnostics.append)

        scheduler.load_from_settings({
            "version": 1,
            "tasks": [
                {"id": "bad", "action": "bad"},
                ScheduledTask.create("ok", "lock", False, TaskTriggerType.COUNTDOWN, {"seconds": 1}, RepeatRule.ONCE, 1).to_dict(),
            ],
        })

        self.assertEqual(len(scheduler.tasks), 1)
        self.assertIn("已忽略无效任务", diagnostics[0])
        self.assertIn("动作无效：bad", diagnostics[0])
        self.assertNotIn("invalid saved task", diagnostics[0])
        self.assertNotIn("invalid action", diagnostics[0])

    def test_load_recomputes_recurring_fixed_time_next_run_even_when_saved_stale(self):
        scheduler = TaskScheduler(now_provider=lambda: datetime(2026, 6, 3, 12, 0, 0))
        saved = {
            "version": 1,
            "tasks": [{
                "id": "daily-1",
                "name": "每天睡眠",
                "action": "sleep",
                "forceClose": False,
                "triggerType": "fixed_time",
                "triggerConfig": {"hour": 8, "minute": 30},
                "repeatRule": "daily",
                "enabled": True,
                "status": "pending",
                "createdOrder": 1,
                "nextRunAt": "2026-06-02T08:30:00",
                "lastRunAt": None,
                "lastError": "",
            }],
        }

        scheduler.load_from_settings(saved)

        task = scheduler.tasks[0]
        self.assertEqual(task.next_run_at, datetime(2026, 6, 4, 8, 30, 0))
        self.assertEqual(scheduler.due_tasks(datetime(2026, 6, 3, 12, 0, 0)), [])

    def test_load_keeps_disabled_recurring_fixed_time_paused(self):
        scheduler = TaskScheduler(now_provider=lambda: datetime(2026, 6, 3, 12, 0, 0))
        saved = {
            "version": 1,
            "tasks": [{
                "id": "daily-paused",
                "name": "暂停每日任务",
                "action": "sleep",
                "forceClose": False,
                "triggerType": "fixed_time",
                "triggerConfig": {"hour": 8, "minute": 30},
                "repeatRule": "daily",
                "enabled": False,
                "status": "pending",
                "createdOrder": 1,
                "nextRunAt": "2026-06-02T08:30:00",
                "lastRunAt": None,
                "lastError": "",
            }],
        }

        scheduler.load_from_settings(saved)

        task = scheduler.tasks[0]
        self.assertIsNone(task.next_run_at)
        self.assertEqual(task.status.value, "paused")


if __name__ == "__main__":
    unittest.main()
