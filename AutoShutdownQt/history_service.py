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


def _limit(settings):
    try:
        value = int(settings.get("taskHistoryLimit", 500))
    except (TypeError, ValueError):
        return 500
    return max(1, value)


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
    return json.dumps(list(reversed(rows)), ensure_ascii=False)


def clear_history(settings):
    settings["taskHistory"] = []


def export_history_json(settings, target):
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = settings.get("taskHistory")
    if not isinstance(rows, list):
        rows = []
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
