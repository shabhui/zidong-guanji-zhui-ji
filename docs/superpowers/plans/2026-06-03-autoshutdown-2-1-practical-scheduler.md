# AutoShutdownQt 2.1 Practical Scheduler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build AutoShutdownQt 2.1 as a dry-run-safe practical scheduler with tray/background operation, recurring fixed-time tasks, a multi-task queue, and release checksum/checklist support.

**Architecture:** Add focused Python modules for task data, scheduling, and tray integration. Keep `controller.py` as the QML bridge: it converts UI requests into scheduler operations, persists queue state through `settings_service.py`, and routes due tasks through the existing dry-run/live execution boundary.

**Tech Stack:** Python 3, PySide6/QML, `unittest`, JSON settings persistence, PyInstaller release packaging.

---

## Safety and execution constraints

- Do not execute real Windows power actions during development or validation.
- Keep controller default `dryRun` as `True`.
- In tests, inject `_power_executor` fakes and assert dry-run log output instead of calling `power_service.execute_power_action()`.
- Do not delete, stage, or commit these untracked screenshots:
  - `AutoShutdownQt/current-render.png`
  - `AutoShutdownQt/e5e8b88f-7acc-4be7-930f-952ad1670984.png`
- Do not push, tag, or upload release artifacts unless explicitly authorized.
- Commit after each task using only the files listed in that task.

## File structure

- Create `AutoShutdownQt/task_model.py`: enums, `ScheduledTask`, serialization/deserialization, task summaries, validation of supported actions/triggers/repeat rules.
- Create `AutoShutdownQt/task_scheduler.py`: queue ownership, next-run calculation, ordering, due-task detection, execution result application, pause/resume, invalid persisted entry diagnostics.
- Create `AutoShutdownQt/tray_service.py`: optional `QSystemTrayIcon` setup, tray menu callbacks, show/hide/pause/resume/cancel/quit wiring.
- Modify `AutoShutdownQt/controller.py`: instantiate scheduler, expose queue properties/slots to QML, bridge due tasks into `_execute_with_script`, preserve old quick slots by creating queue tasks, persist queue settings.
- Modify `AutoShutdownQt/settings_service.py`: add versioned task queue defaults while preserving all 2.0 settings keys.
- Modify `AutoShutdownQt/main.py`: bump version to 2.1, install tray service after QML root object exists, route close-to-tray through controller/tray service.
- Modify `AutoShutdownQt/qml/Main.qml`: title/version text, queue controls, repeat rule controls, close-to-tray copy, queue row actions.
- Modify `AutoShutdownQt/package_release.py`: bump to 2.1, add checksum/checklist generation, include stronger release manifest fields.
- Modify `AutoShutdownQt/AutoShutdownQt-2.0.spec`: either rename to a 2.1 spec in a dedicated task or update packaging constants to use the existing spec only until packaging is refactored. This plan chooses to create `AutoShutdownQt/AutoShutdownQt-2.1.spec` to keep release identity clear.
- Modify tests under `AutoShutdownQt/tests/`: add focused unit coverage for task model/scheduler, controller bridge/persistence, tray service without requiring a real tray, QML static regressions, and release packaging.
- Modify `README.md` and create/modify `RELEASE_NOTES_v2.1.md`: document tray/background, recurrence, queue limitations, dry-run/live-mode safety, and checksum verification.

---

### Task 1: Task model serialization and summaries

**Files:**
- Create: `AutoShutdownQt/task_model.py`
- Create: `AutoShutdownQt/tests/test_task_model.py`

- [ ] **Step 1: Write failing task model tests**

Create `AutoShutdownQt/tests/test_task_model.py`:

```python
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

        self.assertEqual(process_task.trigger_summary(), "进程退出 notepad.exe")
        self.assertEqual(network_task.trigger_summary(), "网络闲置 60 秒")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run model tests and verify failure**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_task_model -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'task_model'`.

- [ ] **Step 3: Implement task model**

Create `AutoShutdownQt/task_model.py`:

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import uuid4


class TaskTriggerType(str, Enum):
    COUNTDOWN = "countdown"
    FIXED_TIME = "fixed_time"
    PROCESS_EXIT = "process_exit"
    NETWORK_IDLE = "network_idle"


class RepeatRule(str, Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKDAYS = "weekdays"
    WEEKENDS = "weekends"


class TaskStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


POWER_ACTIONS = {"shutdown", "sleep", "hibernate", "restart", "logoff", "lock"}


def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _datetime_to_text(value):
    return value.isoformat() if value else None


def _enum_value(enum_type, value, field_name):
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ValueError(f"invalid {field_name}: {value}") from exc


@dataclass
class ScheduledTask:
    id: str
    name: str
    action: str
    force_close: bool
    trigger_type: TaskTriggerType
    trigger_config: dict
    repeat_rule: RepeatRule
    enabled: bool
    status: TaskStatus
    created_order: int
    next_run_at: datetime | None = None
    last_run_at: datetime | None = None
    last_error: str = ""

    @classmethod
    def create(cls, name, action, force_close, trigger_type, trigger_config, repeat_rule, created_order):
        if action not in POWER_ACTIONS:
            raise ValueError(f"invalid action: {action}")
        trigger_type = trigger_type if isinstance(trigger_type, TaskTriggerType) else TaskTriggerType(trigger_type)
        repeat_rule = repeat_rule if isinstance(repeat_rule, RepeatRule) else RepeatRule(repeat_rule)
        if trigger_type != TaskTriggerType.FIXED_TIME and repeat_rule != RepeatRule.ONCE:
            raise ValueError("only fixed_time tasks can repeat in AutoShutdownQt 2.1")
        return cls(
            id=str(uuid4()),
            name=str(name or "计划任务"),
            action=action,
            force_close=bool(force_close),
            trigger_type=trigger_type,
            trigger_config=dict(trigger_config or {}),
            repeat_rule=repeat_rule,
            enabled=True,
            status=TaskStatus.PENDING,
            created_order=int(created_order),
        )

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("task entry must be an object")
        action = data.get("action")
        if action not in POWER_ACTIONS:
            raise ValueError(f"invalid action: {action}")
        trigger_type = _enum_value(TaskTriggerType, data.get("triggerType"), "triggerType")
        repeat_rule = _enum_value(RepeatRule, data.get("repeatRule", RepeatRule.ONCE.value), "repeatRule")
        status = _enum_value(TaskStatus, data.get("status", TaskStatus.PENDING.value), "status")
        if trigger_type != TaskTriggerType.FIXED_TIME and repeat_rule != RepeatRule.ONCE:
            raise ValueError("only fixed_time tasks can repeat in AutoShutdownQt 2.1")
        return cls(
            id=str(data.get("id") or uuid4()),
            name=str(data.get("name") or "计划任务"),
            action=action,
            force_close=bool(data.get("forceClose", False)),
            trigger_type=trigger_type,
            trigger_config=dict(data.get("triggerConfig") or {}),
            repeat_rule=repeat_rule,
            enabled=bool(data.get("enabled", True)),
            status=status,
            created_order=int(data.get("createdOrder", 0)),
            next_run_at=_parse_datetime(data.get("nextRunAt")),
            last_run_at=_parse_datetime(data.get("lastRunAt")),
            last_error=str(data.get("lastError") or ""),
        )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "action": self.action,
            "forceClose": self.force_close,
            "triggerType": self.trigger_type.value,
            "triggerConfig": dict(self.trigger_config),
            "repeatRule": self.repeat_rule.value,
            "enabled": self.enabled,
            "status": self.status.value,
            "createdOrder": self.created_order,
            "nextRunAt": _datetime_to_text(self.next_run_at),
            "lastRunAt": _datetime_to_text(self.last_run_at),
            "lastError": self.last_error,
        }

    def trigger_summary(self):
        if self.trigger_type == TaskTriggerType.COUNTDOWN:
            seconds = int(self.trigger_config.get("seconds", 0))
            minutes = seconds // 60
            if minutes and seconds % 60 == 0:
                return f"倒计时 {minutes} 分钟"
            return f"倒计时 {seconds} 秒"
        if self.trigger_type == TaskTriggerType.FIXED_TIME:
            hour = int(self.trigger_config.get("hour", 0))
            minute = int(self.trigger_config.get("minute", 0))
            return f"固定时间 {hour:02d}:{minute:02d}"
        if self.trigger_type == TaskTriggerType.PROCESS_EXIT:
            return f"进程退出 {self.trigger_config.get('processName', '')}"
        if self.trigger_type == TaskTriggerType.NETWORK_IDLE:
            return f"网络闲置 {int(self.trigger_config.get('idleSeconds', 0))} 秒"
        return self.trigger_type.value

    def repeat_summary(self):
        labels = {
            RepeatRule.ONCE: "仅一次",
            RepeatRule.DAILY: "每天",
            RepeatRule.WEEKDAYS: "工作日",
            RepeatRule.WEEKENDS: "周末",
        }
        return labels[self.repeat_rule]

    def next_run_text(self):
        return self.next_run_at.strftime("%Y-%m-%d %H:%M") if self.next_run_at else "未安排"
```

- [ ] **Step 4: Run model tests and verify pass**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_task_model -v
```

Expected: PASS.

- [ ] **Step 5: Commit task model**

```bash
git add AutoShutdownQt/task_model.py AutoShutdownQt/tests/test_task_model.py
git commit -m "$(cat <<'EOF'
Add AutoShutdownQt 2.1 task model
EOF
)"
```

---

### Task 2: Scheduler recurrence, queue ordering, and due handling

**Files:**
- Create: `AutoShutdownQt/task_scheduler.py`
- Create: `AutoShutdownQt/tests/test_task_scheduler.py`

- [ ] **Step 1: Write failing scheduler tests**

Create `AutoShutdownQt/tests/test_task_scheduler.py`:

```python
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
    def test_countdown_task_gets_next_run_and_completes_after_due(self):
        now = datetime(2026, 6, 3, 12, 0, 0)
        scheduler = TaskScheduler(now_provider=lambda: now)

        task = scheduler.add_task("10 秒后锁定", "lock", False, TaskTriggerType.COUNTDOWN, {"seconds": 10}, RepeatRule.ONCE)

        self.assertEqual(task.next_run_at, now + timedelta(seconds=10))
        due = scheduler.due_tasks(now + timedelta(seconds=10))
        self.assertEqual([item.id for item in due], [task.id])

        scheduler.mark_executed(task.id, now + timedelta(seconds=10), success=True)

        self.assertEqual(scheduler.get_task(task.id).status, TaskStatus.COMPLETED)
        self.assertIsNone(scheduler.get_task(task.id).next_run_at)

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
        self.assertIn("invalid saved task", diagnostics[0])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run scheduler tests and verify failure**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_task_scheduler -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'task_scheduler'`.

- [ ] **Step 3: Implement scheduler**

Create `AutoShutdownQt/task_scheduler.py`:

```python
from datetime import datetime, timedelta

from task_model import RepeatRule, ScheduledTask, TaskStatus, TaskTriggerType


class TaskScheduler:
    def __init__(self, now_provider=None, diagnostic_logger=None):
        self._now_provider = now_provider or datetime.now
        self._diagnostic_logger = diagnostic_logger or (lambda message: None)
        self._tasks = []
        self._next_order = 1
        self._paused = False

    @property
    def tasks(self):
        return list(self._tasks)

    @property
    def paused(self):
        return self._paused

    def add_task(self, name, action, force_close, trigger_type, trigger_config, repeat_rule):
        task = ScheduledTask.create(name, action, force_close, trigger_type, trigger_config, repeat_rule, self._next_order)
        self._next_order += 1
        self._schedule_next_run(task, self._now_provider())
        self._tasks.append(task)
        self._sort_tasks()
        return task

    def get_task(self, task_id):
        for task in self._tasks:
            if task.id == task_id:
                return task
        raise KeyError(task_id)

    def remove_task(self, task_id):
        before = len(self._tasks)
        self._tasks = [task for task in self._tasks if task.id != task_id]
        return len(self._tasks) != before

    def set_enabled(self, task_id, enabled):
        task = self.get_task(task_id)
        task.enabled = bool(enabled)
        if task.enabled and task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            task.status = TaskStatus.PENDING
        if task.enabled:
            self._schedule_next_run(task, self._now_provider())
        self._sort_tasks()
        return task

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def due_tasks(self, now=None):
        if self._paused:
            return []
        now = now or self._now_provider()
        due = [task for task in self._tasks if task.enabled and task.next_run_at and task.next_run_at <= now and task.status in (TaskStatus.PENDING, TaskStatus.ACTIVE)]
        return sorted(due, key=lambda task: (task.next_run_at, task.created_order))

    def mark_executed(self, task_id, executed_at=None, success=True, error=""):
        executed_at = executed_at or self._now_provider()
        task = self.get_task(task_id)
        task.last_run_at = executed_at
        task.last_error = "" if success else str(error or "execution failed")
        if not success:
            task.status = TaskStatus.FAILED
            task.next_run_at = None
        elif task.repeat_rule == RepeatRule.ONCE:
            task.status = TaskStatus.COMPLETED
            task.next_run_at = None
        else:
            task.status = TaskStatus.PENDING
            self._schedule_next_run(task, executed_at + timedelta(seconds=1))
        self._sort_tasks()
        return task

    def to_settings(self):
        return {"version": 1, "tasks": [task.to_dict() for task in self._tasks]}

    def load_from_settings(self, value):
        self._tasks = []
        tasks = value.get("tasks", []) if isinstance(value, dict) else []
        max_order = 0
        for entry in tasks:
            try:
                task = ScheduledTask.from_dict(entry)
                self._schedule_next_run(task, self._now_provider())
            except Exception as exc:
                self._diagnostic_logger(f"invalid saved task ignored: {exc}")
                continue
            self._tasks.append(task)
            max_order = max(max_order, task.created_order)
        self._next_order = max_order + 1
        self._sort_tasks()

    def rows(self):
        return [{
            "id": task.id,
            "name": task.name,
            "action": task.action,
            "forceClose": task.force_close,
            "triggerType": task.trigger_type.value,
            "triggerSummary": task.trigger_summary(),
            "repeatRule": task.repeat_rule.value,
            "repeatSummary": task.repeat_summary(),
            "status": task.status.value,
            "enabled": task.enabled,
            "nextRunText": task.next_run_text(),
            "lastError": task.last_error,
        } for task in self._tasks]

    def _schedule_next_run(self, task, now):
        if not task.enabled or task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            return
        if task.trigger_type == TaskTriggerType.COUNTDOWN:
            task.next_run_at = now + timedelta(seconds=max(1, int(task.trigger_config.get("seconds", 0))))
        elif task.trigger_type == TaskTriggerType.FIXED_TIME:
            task.next_run_at = self._next_fixed_time(task, now)
        else:
            task.next_run_at = None
            task.status = TaskStatus.ACTIVE if task.enabled else TaskStatus.PAUSED

    def _next_fixed_time(self, task, now):
        hour = int(task.trigger_config.get("hour", 0))
        minute = int(task.trigger_config.get("minute", 0))
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        while not self._repeat_allows_day(task.repeat_rule, candidate):
            candidate += timedelta(days=1)
        return candidate

    def _repeat_allows_day(self, repeat_rule, candidate):
        if repeat_rule in (RepeatRule.ONCE, RepeatRule.DAILY):
            return True
        if repeat_rule == RepeatRule.WEEKDAYS:
            return candidate.weekday() < 5
        if repeat_rule == RepeatRule.WEEKENDS:
            return candidate.weekday() >= 5
        return False

    def _sort_tasks(self):
        future = datetime.max
        self._tasks.sort(key=lambda task: (task.next_run_at or future, task.created_order))
```

- [ ] **Step 4: Run scheduler tests and model tests**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_task_model AutoShutdownQt.tests.test_task_scheduler -v
```

Expected: PASS.

- [ ] **Step 5: Commit scheduler**

```bash
git add AutoShutdownQt/task_scheduler.py AutoShutdownQt/tests/test_task_scheduler.py
git commit -m "$(cat <<'EOF'
Add AutoShutdownQt 2.1 task scheduler
EOF
)"
```

---

### Task 3: Settings persistence for versioned task queue

**Files:**
- Modify: `AutoShutdownQt/settings_service.py`
- Modify: `AutoShutdownQt/tests/test_practical_enhancements.py`

- [ ] **Step 1: Write failing persistence tests**

Append these tests inside `PracticalEnhancementsTest` before `if __name__ == "__main__":` in `AutoShutdownQt/tests/test_practical_enhancements.py`:

```python
    def test_default_settings_include_versioned_task_queue(self):
        settings = default_settings()

        self.assertEqual(settings["taskQueue"], {"version": 1, "tasks": []})

    def test_settings_round_trip_preserves_task_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            data = default_settings()
            data["taskQueue"] = {
                "version": 1,
                "tasks": [{
                    "id": "task-1",
                    "name": "测试任务",
                    "action": "lock",
                    "forceClose": False,
                    "triggerType": "countdown",
                    "triggerConfig": {"seconds": 60},
                    "repeatRule": "once",
                    "enabled": True,
                    "status": "pending",
                    "createdOrder": 1,
                    "nextRunAt": None,
                    "lastRunAt": None,
                    "lastError": "",
                }],
            }

            save_settings(data, path)
            loaded = load_settings(path)

            self.assertEqual(loaded["taskQueue"]["version"], 1)
            self.assertEqual(loaded["taskQueue"]["tasks"][0]["id"], "task-1")
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_default_settings_include_versioned_task_queue AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_settings_round_trip_preserves_task_queue -v
```

Expected: FAIL because `taskQueue` is absent.

- [ ] **Step 3: Add task queue default**

Modify `AutoShutdownQt/settings_service.py` `DEFAULT_SETTINGS`:

```python
DEFAULT_SETTINGS = {
    "dryRun": True,
    "forceClose": False,
    "selectedAction": "shutdown",
    "scriptEnabled": False,
    "scriptPath": "",
    "scriptTimeoutSeconds": 10,
    "processName": "",
    "processPollSeconds": 5,
    "networkDownloadThresholdKbps": 10.0,
    "networkUploadThresholdKbps": 10.0,
    "networkIdleSeconds": 60,
    "networkPollSeconds": 3,
    "taskQueue": {"version": 1, "tasks": []},
}
```

Modify `default_settings()` so nested data is not shared:

```python
def default_settings():
    return json.loads(json.dumps(DEFAULT_SETTINGS))
```

- [ ] **Step 4: Run persistence tests**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_default_settings_include_versioned_task_queue AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_settings_round_trip_preserves_task_queue -v
```

Expected: PASS.

- [ ] **Step 5: Commit settings persistence**

```bash
git add AutoShutdownQt/settings_service.py AutoShutdownQt/tests/test_practical_enhancements.py
git commit -m "$(cat <<'EOF'
Persist AutoShutdownQt 2.1 task queue settings
EOF
)"
```

---

### Task 4: Controller bridge for queue tasks and dry-run execution

**Files:**
- Modify: `AutoShutdownQt/controller.py`
- Modify: `AutoShutdownQt/tests/test_practical_enhancements.py`

- [ ] **Step 1: Write failing controller bridge tests**

Append these tests inside `PracticalEnhancementsTest`:

```python
    def test_start_countdown_adds_queue_task_instead_of_replacing_queue(self):
        controller = AppController()

        controller.startCountdown(0, 1, 0)
        controller.startCountdown(0, 2, 0)

        self.assertEqual(controller.queueTaskCount, 2)
        self.assertIn("倒计时 1 分钟", controller.queueText)
        self.assertIn("倒计时 2 分钟", controller.queueText)
        self.assertIn("已加入任务队列", controller.logText)

    def test_fixed_time_repeat_task_can_be_added_from_qml_slot(self):
        controller = AppController()
        controller.selectedAction = "sleep"

        controller.addFixedTimeTask("每天睡眠", 23, 0, "daily")

        self.assertEqual(controller.queueTaskCount, 1)
        self.assertIn("每天睡眠", controller.queueText)
        self.assertIn("每天", controller.queueText)

    def test_due_queue_tasks_execute_through_dry_run_boundary(self):
        controller = AppController()
        controller.startCountdown(0, 0, 1)

        controller._scheduler.get_task(controller._scheduler.tasks[0].id).next_run_at = controller._now()
        controller._on_tick()

        self.assertIn("[dryRun] Would execute: shutdown force=False", controller.logText)
        self.assertIn("completed", controller.queueText)

    def test_queue_persists_when_controller_uses_settings_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            first = AppController(settings_path=path)
            first.startCountdown(0, 1, 0)

            second = AppController(settings_path=path)

            self.assertEqual(second.queueTaskCount, 1)
            self.assertIn("倒计时", second.queueText)
```

- [ ] **Step 2: Run controller bridge tests and verify failure**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_start_countdown_adds_queue_task_instead_of_replacing_queue AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_fixed_time_repeat_task_can_be_added_from_qml_slot AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_due_queue_tasks_execute_through_dry_run_boundary AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_queue_persists_when_controller_uses_settings_path -v
```

Expected: FAIL because queue properties/slots do not exist.

- [ ] **Step 3: Add scheduler imports, signals, construction, and properties**

Modify `AutoShutdownQt/controller.py` imports:

```python
import json
from task_model import RepeatRule, TaskTriggerType
from task_scheduler import TaskScheduler
```

Add signal near the other signals:

```python
    taskQueueChanged = Signal()
```

Add this setup after `self._network_reader = network_reader or NetworkReader()` in `__init__`:

```python
        self._scheduler = TaskScheduler(now_provider=self._now, diagnostic_logger=self._add_log)
        self._scheduler.load_from_settings(settings.get("taskQueue"))
```

Add QML properties after `diagnosticText`:

```python
    def getQueueTaskCount(self):
        return len(self._scheduler.tasks)
    queueTaskCount = Property(int, getQueueTaskCount, notify=taskQueueChanged)

    def getQueueText(self):
        rows = self._scheduler.rows()
        if not rows:
            return "暂无任务"
        return "\n".join(
            f"{row['name']} · {row['triggerSummary']} · {row['repeatSummary']} · {row['status']} · {row['nextRunText']}"
            for row in rows
        )
    queueText = Property(str, getQueueText, notify=taskQueueChanged)

    def getQueueRowsJson(self):
        return json.dumps(self._scheduler.rows(), ensure_ascii=False)
    queueRowsJson = Property(str, getQueueRowsJson, notify=taskQueueChanged)
```

- [ ] **Step 4: Convert countdown/fixed slots into queue operations**

Replace `startCountdown()` body with:

```python
    @Slot(int, int, int)
    def startCountdown(self, hours, minutes, seconds):
        total = hours * 3600 + minutes * 60 + seconds
        if total <= 0:
            self._add_log("倒计时时长无效，已忽略")
            return
        task = self._scheduler.add_task(
            f"{self._format_duration(total)} 后{self.actionLabel}",
            self._selected_action,
            self._force_close,
            TaskTriggerType.COUNTDOWN,
            {"seconds": total},
            RepeatRule.ONCE,
        )
        self._remaining_seconds = total
        self._status = "running"
        self._target_time_str = task.next_run_text()
        self._timer.start()
        self._add_log(f"已加入任务队列：{task.name}")
        self._persist_queue_and_emit()
        self.statusChanged.emit()
        self.remainingTimeChanged.emit()
        self.targetInfoChanged.emit()
```

Replace `startFixedTime()` body with:

```python
    @Slot(int, int)
    def startFixedTime(self, hour, minute):
        self.addFixedTimeTask(f"{hour:02d}:{minute:02d} {self.actionLabel}", hour, minute, "once")
```

Add new slot:

```python
    @Slot(str, int, int, str)
    def addFixedTimeTask(self, name, hour, minute, repeat_rule):
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            self._add_log("指定时间无效，已忽略")
            return
        try:
            repeat = RepeatRule(repeat_rule or "once")
            task = self._scheduler.add_task(
                name or f"{hour:02d}:{minute:02d} {self.actionLabel}",
                self._selected_action,
                self._force_close,
                TaskTriggerType.FIXED_TIME,
                {"hour": hour, "minute": minute},
                repeat,
            )
        except ValueError as exc:
            self._add_log(f"定时任务无效：{exc}")
            return
        self._status = "running"
        self._target_time_str = task.next_run_text()
        self._timer.start()
        self._add_log(f"已加入任务队列：{task.name}")
        self._persist_queue_and_emit()
        self.statusChanged.emit()
        self.targetInfoChanged.emit()
```

- [ ] **Step 5: Add due queue execution and persistence helpers**

Replace `_on_tick()` with:

```python
    def _on_tick(self):
        if self._remaining_seconds > 0:
            self._remaining_seconds -= 1
            self.remainingTimeChanged.emit()
        due_tasks = self._scheduler.due_tasks(self._now())
        if not due_tasks and self._remaining_seconds <= 0:
            self._timer.stop()
            self._status = "ready" if not self._scheduler.tasks else "running"
            self.statusChanged.emit()
            return
        for task in due_tasks:
            old_action = self._selected_action
            old_force = self._force_close
            self._selected_action = task.action
            self._force_close = task.force_close
            try:
                self._execute_with_script(f"任务到期：{task.name}")
                self._scheduler.mark_executed(task.id, self._now(), success=True)
            except Exception as exc:
                self._scheduler.mark_executed(task.id, self._now(), success=False, error=str(exc))
                self._add_log(f"任务执行失败：{task.name}：{exc}")
            finally:
                self._selected_action = old_action
                self._force_close = old_force
        self._persist_queue_and_emit()
        self.statusChanged.emit()
        self.targetInfoChanged.emit()
```

Add helper methods before `_settings_snapshot()`:

```python
    def _now(self):
        return datetime.now()

    def _persist_queue_and_emit(self):
        self._save_settings()
        self.taskQueueChanged.emit()
```

Add `taskQueue` to `_settings_snapshot()`:

```python
            "taskQueue": self._scheduler.to_settings(),
```

- [ ] **Step 6: Run controller bridge tests**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_start_countdown_adds_queue_task_instead_of_replacing_queue AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_fixed_time_repeat_task_can_be_added_from_qml_slot AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_due_queue_tasks_execute_through_dry_run_boundary AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_queue_persists_when_controller_uses_settings_path -v
```

Expected: PASS. If existing replacement tests fail, update them to assert queue addition instead of replacement because 2.1 intentionally supports multiple tasks.

- [ ] **Step 7: Commit controller queue bridge**

```bash
git add AutoShutdownQt/controller.py AutoShutdownQt/tests/test_practical_enhancements.py
git commit -m "$(cat <<'EOF'
Bridge AutoShutdownQt queue tasks through controller
EOF
)"
```

---

### Task 5: Queue management slots and trigger queue representation

**Files:**
- Modify: `AutoShutdownQt/controller.py`
- Modify: `AutoShutdownQt/tests/test_practical_enhancements.py`

- [ ] **Step 1: Write failing queue management tests**

Append these tests inside `PracticalEnhancementsTest`:

```python
    def test_queue_task_can_be_disabled_enabled_and_deleted(self):
        controller = AppController()
        controller.startCountdown(0, 1, 0)
        task_id = controller._scheduler.tasks[0].id

        controller.setQueueTaskEnabled(task_id, False)
        self.assertIn("enabled=false", controller.queueRowsJson)

        controller.setQueueTaskEnabled(task_id, True)
        self.assertIn("enabled=true", controller.queueRowsJson)

        controller.deleteQueueTask(task_id)
        self.assertEqual(controller.queueTaskCount, 0)

    def test_process_trigger_start_adds_active_queue_task(self):
        controller = AppController()
        controller.processName = "notepad.exe"
        controller._process_checker = lambda name: True

        controller.startProcessTrigger()

        self.assertEqual(controller.queueTaskCount, 1)
        self.assertIn("process_exit", controller.queueRowsJson)
        self.assertIn("notepad.exe", controller.queueText)

    def test_network_trigger_start_adds_active_queue_task(self):
        samples = [NetworkSample(True, received_bytes=1, sent_bytes=1, monotonic_seconds=1.0)]
        controller = AppController(network_reader=FakeNetworkReader(samples))

        controller.startNetworkTrigger()

        self.assertEqual(controller.queueTaskCount, 1)
        self.assertIn("network_idle", controller.queueRowsJson)
        self.assertIn("网络闲置", controller.queueText)
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_queue_task_can_be_disabled_enabled_and_deleted AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_process_trigger_start_adds_active_queue_task AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_network_trigger_start_adds_active_queue_task -v
```

Expected: FAIL because management slots and trigger queue rows are absent.

- [ ] **Step 3: Add queue management slots**

Add to `controller.py` slots section:

```python
    @Slot(str, bool)
    def setQueueTaskEnabled(self, task_id, enabled):
        try:
            self._scheduler.set_enabled(task_id, enabled)
        except KeyError:
            self._add_log(f"任务不存在：{task_id}")
            return
        self._add_log("任务已启用" if enabled else "任务已禁用")
        self._persist_queue_and_emit()

    @Slot(str)
    def deleteQueueTask(self, task_id):
        removed = self._scheduler.remove_task(task_id)
        if not removed:
            self._add_log(f"任务不存在：{task_id}")
            return
        self._add_log("任务已删除")
        self._persist_queue_and_emit()

    @Slot(str)
    def runQueueTaskDryRunCheck(self, task_id):
        try:
            task = self._scheduler.get_task(task_id)
        except KeyError:
            self._add_log(f"任务不存在：{task_id}")
            return
        self._add_log(f"Dry-run 检查：{task.name} -> {task.action} force={task.force_close}")
```

- [ ] **Step 4: Add trigger queue rows when starting process/network triggers**

In `startProcessTrigger()`, after successful activation and before `self.processTriggerChanged.emit()`, add:

```python
        self._scheduler.add_task(
            f"进程退出：{name}",
            self._selected_action,
            self._force_close,
            TaskTriggerType.PROCESS_EXIT,
            {"processName": name, "pollSeconds": self._process_poll_seconds},
            RepeatRule.ONCE,
        )
        self._persist_queue_and_emit()
```

In `startNetworkTrigger()`, after successful activation and before `self.networkTriggerChanged.emit()`, add:

```python
        self._scheduler.add_task(
            "网络闲置触发",
            self._selected_action,
            self._force_close,
            TaskTriggerType.NETWORK_IDLE,
            {
                "downloadKbps": self._network_download_threshold_kbps,
                "uploadKbps": self._network_upload_threshold_kbps,
                "idleSeconds": self._network_idle_seconds,
                "pollSeconds": self._network_poll_seconds,
            },
            RepeatRule.ONCE,
        )
        self._persist_queue_and_emit()
```

- [ ] **Step 5: Run queue management tests**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_queue_task_can_be_disabled_enabled_and_deleted AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_process_trigger_start_adds_active_queue_task AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_network_trigger_start_adds_active_queue_task -v
```

Expected: PASS.

- [ ] **Step 6: Commit queue management bridge**

```bash
git add AutoShutdownQt/controller.py AutoShutdownQt/tests/test_practical_enhancements.py
git commit -m "$(cat <<'EOF'
Add queue management slots for AutoShutdownQt 2.1
EOF
)"
```

---

### Task 6: QML queue and recurrence controls

**Files:**
- Modify: `AutoShutdownQt/qml/Main.qml`
- Modify: `AutoShutdownQt/tests/test_e5e8_ui_regressions.py`

- [ ] **Step 1: Write failing QML static regression test**

Append this test inside `E5E8ButtonRegressionTest`:

```python
    def test_2_1_queue_and_repeat_controls_are_wired(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        for snippet in (
            "AutoShutdown v2.1",
            "v2.1 · Practical Scheduler",
            "controller.queueRowsJson",
            "JSON.parse(controller.queueRowsJson)",
            "controller.addFixedTimeTask(",
            "controller.setQueueTaskEnabled(",
            "controller.deleteQueueTask(",
            "controller.runQueueTaskDryRunCheck(",
            "repeatRuleCombo",
        ):
            self.assertIn(snippet, main)
        for label in ("任务队列", "重复规则", "仅一次", "每天", "工作日", "周末", "Dry-run 检查", "删除"):
            self.assertIn(label, main)
```

- [ ] **Step 2: Run QML regression and verify failure**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_e5e8_ui_regressions.E5E8ButtonRegressionTest.test_2_1_queue_and_repeat_controls_are_wired -v
```

Expected: FAIL because QML still shows 2.0 and has no queue controls.

- [ ] **Step 3: Update title/version text and add queue parser helper**

In `Main.qml`, update:

```qml
title: "AutoShutdown v2.1"
```

Update subtitle text:

```qml
text: "v2.1 · Practical Scheduler"
```

Add helper function near `safeFloat()`:

```qml
    function queueRows() {
        try {
            return JSON.parse(controller.queueRowsJson)
        } catch (error) {
            return []
        }
    }
```

- [ ] **Step 4: Add repeat controls to Timer page fixed-time card**

In the fixed-time card after `TimeInputPanel { id: fixedInput ... }`, insert:

```qml
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10
                            Text { text: "重复规则"; color: Theme.textSecondary; font.pixelSize: 13 }
                            ComboBox {
                                id: repeatRuleCombo
                                Layout.preferredWidth: 150
                                model: [
                                    { label: "仅一次", value: "once" },
                                    { label: "每天", value: "daily" },
                                    { label: "工作日", value: "weekdays" },
                                    { label: "周末", value: "weekends" }
                                ]
                                textRole: "label"
                                valueRole: "value"
                            }
                        }
```

Change the fixed-time button click to:

```qml
onClicked: controller.addFixedTimeTask("固定时间任务", mainWindow.safeInt(fixedInput.hours, 23), mainWindow.safeInt(fixedInput.minutes, 0), repeatRuleCombo.currentValue)
```

- [ ] **Step 5: Replace Tasks page placeholder with queue view and row actions**

Inside Tasks page `ColumnLayout`, after the template `GridLayout`, insert:

```qml
                    Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.e5BorderSoft; opacity: 0.62 }
                    Text { text: "任务队列"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: mainWindow.queueRows()
                        delegate: Rectangle {
                            width: ListView.view.width
                            height: 78
                            radius: Theme.radiusMd
                            color: Theme.glassSoft
                            border.color: Theme.e5BorderSoft
                            border.width: 1
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 10
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2
                                    Text { text: modelData.name; color: Theme.textPrimary; font.pixelSize: 14; font.weight: Font.Bold; elide: Text.ElideRight; Layout.fillWidth: true }
                                    Text { text: modelData.triggerSummary + " · " + modelData.repeatSummary; color: Theme.textSecondary; font.pixelSize: 12; elide: Text.ElideRight; Layout.fillWidth: true }
                                    Text { text: modelData.status + " · " + modelData.nextRunText; color: modelData.enabled ? Theme.warning : Theme.textSecondary; font.pixelSize: 12; elide: Text.ElideRight; Layout.fillWidth: true }
                                }
                                FluentSwitch { checked: modelData.enabled; onCheckedChanged: controller.setQueueTaskEnabled(modelData.id, checked) }
                                NeonButton { Layout.preferredWidth: 110; Layout.preferredHeight: 34; compact: true; variant: "secondary"; text: "Dry-run 检查"; onClicked: controller.runQueueTaskDryRunCheck(modelData.id) }
                                NeonButton { Layout.preferredWidth: 70; Layout.preferredHeight: 34; compact: true; variant: "danger"; text: "删除"; onClicked: controller.deleteQueueTask(modelData.id) }
                            }
                        }
                    }
```

Keep existing action tiles and immediate execution controls if space allows; otherwise move them below the queue in a `ScrollView`. Do not remove the existing quick templates.

- [ ] **Step 6: Run QML regression tests**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_e5e8_ui_regressions -v
```

Expected: PASS. If existing count expectations fail because new `NeonButton` controls were added, increase expected minimums only; do not weaken wiring assertions.

- [ ] **Step 7: Commit QML queue controls**

```bash
git add AutoShutdownQt/qml/Main.qml AutoShutdownQt/tests/test_e5e8_ui_regressions.py
git commit -m "$(cat <<'EOF'
Add AutoShutdownQt 2.1 queue controls
EOF
)"
```

---

### Task 7: Tray service and close-to-tray behavior

**Files:**
- Create: `AutoShutdownQt/tray_service.py`
- Create: `AutoShutdownQt/tests/test_tray_service.py`
- Modify: `AutoShutdownQt/main.py`
- Modify: `AutoShutdownQt/controller.py`
- Modify: `AutoShutdownQt/qml/Main.qml`

- [ ] **Step 1: Write failing tray service tests**

Create `AutoShutdownQt/tests/test_tray_service.py`:

```python
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
sys.path.insert(0, str(APP_DIR))

from tray_service import TrayService


class FakeWindow:
    def __init__(self):
        self.visible = True
        self.show_calls = 0
        self.hide_calls = 0

    def show(self):
        self.visible = True
        self.show_calls += 1

    def hide(self):
        self.visible = False
        self.hide_calls += 1


class FakeController:
    def __init__(self):
        self.paused = False
        self.cancelled = False
        self.quit_requested = False

    def pauseScheduling(self):
        self.paused = True

    def resumeScheduling(self):
        self.paused = False

    def cancelAllTasks(self):
        self.cancelled = True

    def requestQuit(self):
        self.quit_requested = True


class TrayServiceTest(unittest.TestCase):
    def test_show_hide_pause_resume_cancel_and_quit_callbacks(self):
        window = FakeWindow()
        controller = FakeController()
        service = TrayService(controller, window, tray_factory=lambda: None)

        service.hide_window()
        service.show_window()
        service.pause_or_resume()
        service.cancel_all()
        service.quit_app()

        self.assertEqual(window.hide_calls, 1)
        self.assertEqual(window.show_calls, 1)
        self.assertTrue(controller.paused)
        self.assertTrue(controller.cancelled)
        self.assertTrue(controller.quit_requested)

    def test_unavailable_tray_keeps_window_mode_usable(self):
        window = FakeWindow()
        controller = FakeController()
        messages = []

        service = TrayService(controller, window, tray_factory=lambda: None, logger=messages.append)
        available = service.setup()

        self.assertFalse(available)
        self.assertIn("tray unavailable", messages[0])
```

- [ ] **Step 2: Run tray tests and verify failure**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_tray_service -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tray_service'`.

- [ ] **Step 3: Implement tray service**

Create `AutoShutdownQt/tray_service.py`:

```python
class TrayService:
    def __init__(self, controller, window, tray_factory=None, logger=None):
        self._controller = controller
        self._window = window
        self._tray_factory = tray_factory
        self._logger = logger or (lambda message: None)
        self._tray = None
        self.available = False

    def setup(self):
        try:
            if self._tray_factory is None:
                from PySide6.QtGui import QIcon
                from PySide6.QtWidgets import QMenu, QSystemTrayIcon
                tray = QSystemTrayIcon(QIcon(), None)
                menu = QMenu()
                menu.addAction("Show/Hide", self.toggle_window)
                menu.addAction("Pause/Resume scheduling", self.pause_or_resume)
                menu.addAction("Cancel all tasks", self.cancel_all)
                menu.addAction("Quit", self.quit_app)
                tray.setContextMenu(menu)
                tray.setToolTip("AutoShutdownQt 2.1")
                tray.show()
                self._tray = tray
            else:
                self._tray = self._tray_factory()
        except Exception as exc:
            self._logger(f"tray unavailable: {exc}")
            self.available = False
            return False
        if self._tray is None:
            self._logger("tray unavailable: no tray object")
            self.available = False
            return False
        self.available = True
        return True

    def show_window(self):
        self._window.show()

    def hide_window(self):
        self._window.hide()

    def toggle_window(self):
        if getattr(self._window, "visible", True):
            self.hide_window()
        else:
            self.show_window()

    def pause_or_resume(self):
        if getattr(self._controller, "schedulingPaused", False):
            self._controller.resumeScheduling()
        else:
            self._controller.pauseScheduling()

    def cancel_all(self):
        self._controller.cancelAllTasks()

    def quit_app(self):
        self._controller.requestQuit()
```

- [ ] **Step 4: Add controller tray slots**

In `controller.py`, add signal:

```python
    schedulingPausedChanged = Signal()
```

Add property and slots:

```python
    def getSchedulingPaused(self):
        return self._scheduler.paused
    schedulingPaused = Property(bool, getSchedulingPaused, notify=schedulingPausedChanged)

    @Slot()
    def pauseScheduling(self):
        self._scheduler.pause()
        self._add_log("调度已暂停")
        self.schedulingPausedChanged.emit()
        self.taskQueueChanged.emit()

    @Slot()
    def resumeScheduling(self):
        self._scheduler.resume()
        self._add_log("调度已恢复")
        self.schedulingPausedChanged.emit()
        self.taskQueueChanged.emit()

    @Slot()
    def cancelAllTasks(self):
        for task in list(self._scheduler.tasks):
            self._scheduler.remove_task(task.id)
        self.cancel()
        self._add_log("已取消所有任务")
        self._persist_queue_and_emit()

    @Slot()
    def requestQuit(self):
        active = [task for task in self._scheduler.tasks if task.enabled]
        if active:
            self._add_log("退出前请确认：仍有启用任务")
        QCoreApplication.quit()
```

- [ ] **Step 5: Wire tray service in main**

Modify `AutoShutdownQt/main.py` imports:

```python
from PySide6.QtWidgets import QApplication
from tray_service import TrayService
```

Change app construction:

```python
    app = QApplication(sys.argv)
```

After `engine.rootObjects()` check, add:

```python
    window = engine.rootObjects()[0]
    tray_service = TrayService(controller, window, logger=controller._add_log)
    controller.trayService = tray_service
    tray_service.setup()
```

- [ ] **Step 6: Add close-to-tray QML copy and close interception**

In `Main.qml`, add:

```qml
    property bool trayCloseRequested: false
    onClosing: function(close) {
        if (!trayCloseRequested) {
            close.accepted = false
            mainWindow.hide()
        }
    }
```

Update settings safety text to include:

```qml
关闭窗口会隐藏到托盘；请使用托盘菜单 Quit 显式退出。
```

- [ ] **Step 7: Run tray and controller tests**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_tray_service AutoShutdownQt.tests.test_practical_enhancements -v
```

Expected: PASS.

- [ ] **Step 8: Commit tray service**

```bash
git add AutoShutdownQt/tray_service.py AutoShutdownQt/tests/test_tray_service.py AutoShutdownQt/main.py AutoShutdownQt/controller.py AutoShutdownQt/qml/Main.qml
git commit -m "$(cat <<'EOF'
Add AutoShutdownQt 2.1 tray background service
EOF
)"
```

---

### Task 8: Release checksum, checklist, manifest, and version identity

**Files:**
- Modify: `AutoShutdownQt/package_release.py`
- Create: `AutoShutdownQt/AutoShutdownQt-2.1.spec`
- Modify: `AutoShutdownQt/tests/test_release_packaging.py`
- Modify: `.gitignore`
- Modify: `AutoShutdownQt/main.py`

- [ ] **Step 1: Write failing packaging tests**

Append these tests inside `ReleasePackagingTest`:

```python
    def test_main_declares_final_2_1_version(self):
        main = MAIN_PY.read_text(encoding="utf-8")
        self.assertIn('app.setApplicationVersion("2.1")', main)

    def test_release_script_builds_2_1_checksum_and_checklist(self):
        script = PACKAGE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn('VERSION = "2.1"', script)
        self.assertIn('AutoShutdownQt-2.1.zip', script)
        self.assertIn('SHA256SUMS.txt', script)
        self.assertIn('release-checklist-v2.1.md', script)
        self.assertIn('create_sha256sums', script)
        self.assertIn('create_release_checklist', script)

    def test_checksum_file_contains_archive_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "AutoShutdownQt-2.1.zip"
            archive_path.write_bytes(b"demo")

            sums = package_release.create_sha256sums(archive_path, Path(tmp) / "SHA256SUMS.txt")
            content = sums.read_text(encoding="utf-8")

            self.assertIn("AutoShutdownQt-2.1.zip", content)
            self.assertRegex(content, r"^[0-9a-f]{64}  AutoShutdownQt-2.1.zip")

    def test_release_checklist_mentions_dry_run_and_no_real_power_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            checklist = package_release.create_release_checklist(Path(tmp) / "release-checklist-v2.1.md")
            content = checklist.read_text(encoding="utf-8")

            self.assertIn("Dry-run", content)
            self.assertIn("Do not execute real shutdown", content)
            self.assertIn("SHA256SUMS.txt", content)
```

- [ ] **Step 2: Run packaging tests and verify failure**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_release_packaging.ReleasePackagingTest.test_main_declares_final_2_1_version AutoShutdownQt.tests.test_release_packaging.ReleasePackagingTest.test_release_script_builds_2_1_checksum_and_checklist AutoShutdownQt.tests.test_release_packaging.ReleasePackagingTest.test_checksum_file_contains_archive_hash AutoShutdownQt.tests.test_release_packaging.ReleasePackagingTest.test_release_checklist_mentions_dry_run_and_no_real_power_actions -v
```

Expected: FAIL because packaging is still 2.0 and helpers are absent.

- [ ] **Step 3: Create 2.1 spec by copying/updating 2.0 spec**

Create `AutoShutdownQt/AutoShutdownQt-2.1.spec` with the same structure as `AutoShutdownQt/AutoShutdownQt-2.0.spec`, but update bundle names to `AutoShutdownQt-2.1` and include hidden imports:

```python
hiddenimports=[
    "controller",
    "settings_service",
    "network_service",
    "power_service",
    "script_service",
    "task_model",
    "task_scheduler",
    "tray_service",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuickControls2",
    "PySide6.QtWidgets",
]
```

- [ ] **Step 4: Update package release constants and helpers**

Modify `package_release.py` constants:

```python
import hashlib

VERSION = "2.1"
SPEC_FILE = APP_DIR / "AutoShutdownQt-2.1.spec"
APP_BUNDLE_DIR = DIST_DIR / "AutoShutdownQt-2.1"
ZIP_PATH = DIST_DIR / "AutoShutdownQt-2.1.zip"
SHA256SUMS_PATH = DIST_DIR / "SHA256SUMS.txt"
RELEASE_CHECKLIST_PATH = DIST_DIR / "release-checklist-v2.1.md"
```

Add helpers before `main()`:

```python
def create_sha256sums(archive_path=ZIP_PATH, target_path=SHA256SUMS_PATH):
    archive = Path(archive_path)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    target = Path(target_path)
    target.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    return target


def create_release_checklist(target_path=RELEASE_CHECKLIST_PATH):
    target = Path(target_path)
    target.write_text(
        "# AutoShutdownQt 2.1 Release Checklist\n\n"
        "- [ ] Launch app with Dry-run enabled by default.\n"
        "- [ ] Verify countdown task logs dry-run output only.\n"
        "- [ ] Verify fixed-time daily/weekday/weekend tasks compute next run.\n"
        "- [ ] Verify close hides to tray and tray Quit exits explicitly.\n"
        "- [ ] Do not execute real shutdown, restart, sleep, hibernate, logoff, or lock during validation.\n"
        "- [ ] Publish SHA256SUMS.txt next to the zip.\n",
        encoding="utf-8",
    )
    return target
```

Update `create_release_manifest()` safety notes and checks to include 2.1 support:

```python
        "checks": {
            "executablePresent": (bundle / "AutoShutdownQt.exe").exists(),
            "mainQmlPresent": any(path.exists() for path in main_qml_candidates),
            "taskSchedulerIncluded": True,
        },
        "safetyNotes": [
            "Dry-run is enabled by default.",
            "Live mode can execute real Windows power actions.",
            "Tray/background scheduling continues while the window is hidden.",
            "The portable exe is not code signed.",
        ],
```

Update `main()` after `validate_zip_contents(zip_path)`:

```python
    sums_path = create_sha256sums(zip_path)
    checklist_path = create_release_checklist()
    print(f"Created checksums: {sums_path}")
    print(f"Created release checklist: {checklist_path}")
```

- [ ] **Step 5: Update app version and gitignore exception**

In `main.py`:

```python
app.setApplicationVersion("2.1")
```

In `.gitignore`, add:

```gitignore
!AutoShutdownQt/AutoShutdownQt-2.1.spec
```

- [ ] **Step 6: Run packaging tests**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_release_packaging -v
```

Expected: PASS. Update older 2.0 assertions to 2.1 where they describe current release identity.

- [ ] **Step 7: Commit release support**

```bash
git add AutoShutdownQt/package_release.py AutoShutdownQt/AutoShutdownQt-2.1.spec AutoShutdownQt/tests/test_release_packaging.py AutoShutdownQt/main.py .gitignore
git commit -m "$(cat <<'EOF'
Add AutoShutdownQt 2.1 release checks
EOF
)"
```

---

### Task 9: README and 2.1 release notes

**Files:**
- Modify: `README.md`
- Create: `RELEASE_NOTES_v2.1.md`
- Modify: `AutoShutdownQt/tests/test_release_packaging.py`

- [ ] **Step 1: Write failing docs tests**

Append this test inside `ReleasePackagingTest`:

```python
    def test_2_1_docs_cover_tray_queue_recurrence_and_checksum(self):
        readme = README.read_text(encoding="utf-8")
        notes = (ROOT / "RELEASE_NOTES_v2.1.md").read_text(encoding="utf-8")
        combined = readme + "\n" + notes

        for text in ("AutoShutdownQt 2.1", "系统托盘", "任务队列", "每天", "工作日", "周末", "Dry-run", "SHA256SUMS.txt"):
            self.assertIn(text, combined)
        self.assertIn("dist/AutoShutdownQt-2.1.zip", notes)
```

- [ ] **Step 2: Run docs test and verify failure**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_release_packaging.ReleasePackagingTest.test_2_1_docs_cover_tray_queue_recurrence_and_checksum -v
```

Expected: FAIL because v2.1 release notes do not exist yet.

- [ ] **Step 3: Update README**

Add/update a release section in `README.md` containing:

```markdown
## AutoShutdownQt 2.1

AutoShutdownQt 2.1 adds practical scheduler behavior while keeping Dry-run enabled by default.

- 系统托盘/后台运行：关闭窗口会隐藏到托盘，使用托盘 Quit 显式退出。
- 任务队列：倒计时、固定时间、进程退出、网络闲置任务可在队列中查看、启用/禁用、删除和 Dry-run 检查。
- 重复固定时间：支持仅一次、每天、工作日、周末；倒计时在 2.1 中仍是一次性任务。
- 安全限制：Dry-run 默认开启；LIVE MODE 会执行真实系统动作，验证 release 时不要执行真实关机、重启、睡眠、休眠、注销或锁定。
- 校验：下载 `dist/AutoShutdownQt-2.1.zip` 后使用 `SHA256SUMS.txt` 核对 SHA256。
```

- [ ] **Step 4: Create release notes**

Create `RELEASE_NOTES_v2.1.md`:

```markdown
# AutoShutdownQt 2.1 Release Notes

## Highlights

- 系统托盘/后台运行：窗口关闭后隐藏到托盘，调度继续运行，托盘菜单提供 Show/Hide、Pause/Resume、Cancel all tasks、Quit。
- 任务队列：支持多个倒计时和固定时间任务，队列中可查看状态、下一次运行时间、启用/禁用、删除和 Dry-run 检查。
- 重复固定时间：支持仅一次、每天、工作日、周末。倒计时任务在 2.1 中保持一次性。
- 智能触发队列化：进程退出和网络闲置触发会以队列任务显示；同类触发在 2.1 中一次只保留一个活动监控。

## Safety

Dry-run remains enabled by default. LIVE MODE can execute real Windows power actions. During release validation, do not execute real shutdown, restart, sleep, hibernate, logoff, or lock actions.

## Download and checksum

Expected portable archive:

```text
dist/AutoShutdownQt-2.1.zip
```

Verify the archive against:

```text
dist/SHA256SUMS.txt
```

## Known limitations

- No installer, code signing, startup integration, or automatic online updates in 2.1.
- No complex calendar recurrence rules beyond daily/weekdays/weekends fixed time.
- If multiple live-mode power actions become due together, the first actionable task may end the session before later tasks can run.
```

- [ ] **Step 5: Run docs test**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_release_packaging.ReleasePackagingTest.test_2_1_docs_cover_tray_queue_recurrence_and_checksum -v
```

Expected: PASS.

- [ ] **Step 6: Commit docs**

```bash
git add README.md RELEASE_NOTES_v2.1.md AutoShutdownQt/tests/test_release_packaging.py
git commit -m "$(cat <<'EOF'
Document AutoShutdownQt 2.1 scheduler release
EOF
)"
```

---

### Task 10: Full dry-run verification and implementation handoff checks

**Files:**
- Modify only if tests reveal a bug in files touched by prior tasks.

- [ ] **Step 1: Run full unit test suite**

Run:

```bash
python -m unittest discover AutoShutdownQt/tests -v
```

Expected: PASS.

- [ ] **Step 2: Run packaging helper checks without building PyInstaller**

Run:

```bash
python - <<'PY'
import tempfile
import zipfile
from pathlib import Path
import sys
sys.path.insert(0, 'AutoShutdownQt')
import package_release

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    archive = tmp / 'AutoShutdownQt-2.1.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        z.writestr('AutoShutdownQt-2.1/AutoShutdownQt.exe', 'exe')
        z.writestr('AutoShutdownQt-2.1/_internal/qml/Main.qml', 'qml')
        z.writestr('AutoShutdownQt-2.1/release-manifest.json', '{"app":"AutoShutdownQt","version":"2.1","bundle":"AutoShutdownQt-2.1","executable":"AutoShutdownQt.exe","archive":"AutoShutdownQt-2.1.zip","checks":{"executablePresent":true,"mainQmlPresent":true,"taskSchedulerIncluded":true},"safetyNotes":["Dry-run is enabled by default."]}')
    assert package_release.validate_zip_contents(archive)
    assert package_release.create_sha256sums(archive, tmp / 'SHA256SUMS.txt').exists()
    assert package_release.create_release_checklist(tmp / 'release-checklist-v2.1.md').exists()
print('packaging helper checks passed')
PY
```

Expected: prints `packaging helper checks passed`.

- [ ] **Step 3: Run dry-run-only controller smoke check**

Run:

```bash
python - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, 'AutoShutdownQt')
from controller import AppController

controller = AppController()
assert controller.dryRun is True
controller.startCountdown(0, 0, 1)
for task in controller._scheduler.tasks:
    task.next_run_at = controller._now()
controller._on_tick()
assert '[dryRun] Would execute' in controller.logText
print('dry-run controller smoke passed')
PY
```

Expected: prints dry-run log and `dry-run controller smoke passed`. This must not call real power actions.

- [ ] **Step 4: Check git status excludes screenshots from commits**

Run:

```bash
git status --short
```

Expected: the two screenshots may remain untracked; do not stage them:

```text
?? AutoShutdownQt/current-render.png
?? AutoShutdownQt/e5e8b88f-7acc-4be7-930f-952ad1670984.png
```

- [ ] **Step 5: Commit any final fixes only if needed**

If Step 1-3 required fixes, commit only the touched source/test/doc files:

```bash
git add <specific-fixed-files>
git commit -m "$(cat <<'EOF'
Stabilize AutoShutdownQt 2.1 scheduler tests
EOF
)"
```

If no fixes were needed, do not create an empty commit.

---

## Self-review results

- Spec coverage: tray/background behavior is covered by Task 7; recurring fixed-time tasks and queue ordering are covered by Tasks 1-6; persistence is covered by Tasks 3-5; dry-run-safe execution remains through controller `_execute_with_script` in Task 4; release checksum/checklist/manifest are covered by Task 8; README/release notes are covered by Task 9; dry-run-only validation is covered by Task 10.
- Placeholder scan: no `TBD`, `TODO`, `implement later`, or unspecified "write tests" steps remain. Each implementation task includes concrete tests, commands, expected outcomes, and code snippets.
- Type consistency: task enum values use `countdown`, `fixed_time`, `process_exit`, `network_idle`; repeat values use `once`, `daily`, `weekdays`, `weekends`; QML/controller slots use `addFixedTimeTask`, `setQueueTaskEnabled`, `deleteQueueTask`, and `runQueueTaskDryRunCheck` consistently.
