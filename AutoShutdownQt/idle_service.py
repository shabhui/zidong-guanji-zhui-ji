from dataclasses import dataclass
import ctypes


@dataclass(frozen=True)
class IdleSample:
    available: bool
    idle_seconds: int
    message: str = ""


class WindowsIdleReader:
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

    def sample(self):
        try:
            info = self.LASTINPUTINFO()
            info.cbSize = ctypes.sizeof(info)
            if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
                return IdleSample(False, 0, "GetLastInputInfo failed")
            tick_count = ctypes.windll.kernel32.GetTickCount()
            idle_ms = (tick_count - info.dwTime) & 0xFFFFFFFF
            return IdleSample(True, int(idle_ms / 1000), "")
        except Exception as exc:
            return IdleSample(False, 0, str(exc))


IDLE_ERROR_LABELS = {
    "": "原因未知",
    "unknown": "原因未知",
    "idle unavailable": "系统未提供空闲状态",
    "getlastinputinfo failed": "系统未返回最近输入时间",
}


def _idle_error_text(message):
    text = str(message or "").strip()
    return IDLE_ERROR_LABELS.get(text.lower(), text or IDLE_ERROR_LABELS[""])


def format_idle_status(idle_seconds, threshold_seconds, message=""):
    if idle_seconds is None:
        return f"空闲检测不可用：{_idle_error_text(message)}"
    threshold_minutes = max(1, int(threshold_seconds / 60))
    idle_minutes = min(threshold_minutes, int(idle_seconds / 60))
    return f"已空闲 {idle_minutes} / {threshold_minutes} 分钟"
