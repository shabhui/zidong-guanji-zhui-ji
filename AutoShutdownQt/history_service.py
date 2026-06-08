from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class HistoryEvent:
    timestamp: str
    event: str
    action: str
    source: str
    mode: str
    task_id: str
    message: str


EVENT_LABELS = {
    "created": "已创建",
    "snoozed": "已延后",
    "cancelled": "已取消",
    "reminder": "执行提醒",
    "dry-run": "安全验证",
    "completed": "已完成",
    "failed": "失败",
}

ACTION_LABELS = {
    "shutdown": "关机",
    "sleep": "睡眠",
    "hibernate": "休眠",
    "restart": "重启",
    "logoff": "注销",
    "lock": "锁定",
}

SOURCE_LABELS = {
    "countdown": "手动倒计时",
    "clock": "指定时间",
    "fixed-time": "固定时间",
    "fixed_time": "固定时间",
    "template": "模板任务",
    "process": "进程退出触发",
    "process_exit": "进程退出触发",
    "network": "网络闲置触发",
    "network_idle": "网络闲置触发",
    "idle": "空闲触发",
    "queue": "队列任务",
    "queue-retry": "队列重试",
    "reminder": "执行前提醒",
    "active-countdown": "手动倒计时",
}

MODE_LABELS = {
    "dry-run": "安全验证",
    "live": "真实执行",
}


def _limit(settings):
    try:
        value = int(settings.get("taskHistoryLimit", 500))
    except (TypeError, ValueError):
        return 500
    return max(1, value)


def _label(labels, value):
    text = str(value or "")
    return labels.get(text, text)


def _display_row(row):
    if not isinstance(row, dict):
        return row
    display = dict(row)
    display["eventLabel"] = _label(EVENT_LABELS, row.get("event"))
    display["actionLabel"] = _label(ACTION_LABELS, row.get("action"))
    display["sourceLabel"] = _label(SOURCE_LABELS, row.get("source"))
    display["modeLabel"] = _label(MODE_LABELS, row.get("mode"))
    return display


def _display_rows(rows):
    return [_display_row(row) for row in rows]


def append_history_event(settings, event):
    rows = settings.setdefault("taskHistory", [])
    rows.append(asdict(event))
    keep = _limit(settings)
    if len(rows) > keep:
        del rows[: len(rows) - keep]
    return rows[-1]


def history_rows_json(settings):
    rows = settings.get("taskHistory")
    if not isinstance(rows, list):
        rows = []
    return json.dumps(_display_rows(reversed(rows)), ensure_ascii=False)


def clear_history(settings):
    settings["taskHistory"] = []


def export_history_json(settings, target):
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = settings.get("taskHistory")
    if not isinstance(rows, list):
        rows = []
    path.write_text(json.dumps(_display_rows(rows), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
