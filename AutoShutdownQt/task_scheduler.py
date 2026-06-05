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
        if not task.enabled:
            task.status = TaskStatus.PAUSED
            task.next_run_at = None
        else:
            task.status = TaskStatus.PENDING
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
        due = [
            task for task in self._tasks
            if task.enabled
            and task.next_run_at
            and task.next_run_at <= now
            and task.status in (TaskStatus.PENDING, TaskStatus.ACTIVE)
        ]
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
                self._normalize_loaded_task(task)
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

    def _normalize_loaded_task(self, task):
        if not task.enabled:
            task.status = TaskStatus.PAUSED
            task.next_run_at = None
        elif task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            task.next_run_at = None
        elif task.trigger_type == TaskTriggerType.FIXED_TIME and task.repeat_rule != RepeatRule.ONCE:
            task.status = TaskStatus.PENDING
            self._schedule_next_run(task, self._now_provider())
        elif task.next_run_at is None:
            self._schedule_next_run(task, self._now_provider())

    def _schedule_next_run(self, task, now):
        if not task.enabled or task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            return
        if task.trigger_type == TaskTriggerType.COUNTDOWN:
            task.next_run_at = now + timedelta(seconds=max(1, int(task.trigger_config.get("seconds", 0))))
        elif task.trigger_type == TaskTriggerType.FIXED_TIME:
            task.next_run_at = self._next_fixed_time(task, now)
        elif task.trigger_type == TaskTriggerType.IDLE:
            task.next_run_at = now
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
