from dataclasses import dataclass
from typing import Callable, Optional


PowerActionCompletion = Callable[[bool, str], None]


@dataclass(frozen=True)
class PowerActionContext:
    reason: str
    action: str
    force_close: bool
    close_apps_timeout_seconds: int
    completion: Optional[PowerActionCompletion] = None
    source: str = ""
    task_id: str = ""
