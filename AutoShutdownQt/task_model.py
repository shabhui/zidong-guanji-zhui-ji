from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import uuid4


class TaskTriggerType(str, Enum):
    COUNTDOWN = "countdown"
    FIXED_TIME = "fixed_time"
    PROCESS_EXIT = "process_exit"
    NETWORK_IDLE = "network_idle"
    IDLE = "idle"


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
            raise ValueError("only fixed_time tasks can repeat")
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
            raise ValueError("only fixed_time tasks can repeat")
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
        if self.trigger_type == TaskTriggerType.IDLE:
            return f"空闲 {int(self.trigger_config.get('idleMinutes', 0))} 分钟"
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
