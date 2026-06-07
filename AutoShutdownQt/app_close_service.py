"""Gracefully close running user applications before a power action.

This mimics what Windows does during a normal, user-initiated shutdown: every
visible top-level application window is politely asked to close (``WM_CLOSE``),
so each app still gets the chance to show its own "save your work?" dialog.
Nothing is force-killed here -- if the user also enables "强制关闭应用"
(force close), the operating system's ``shutdown /f`` handles any stragglers.

The Windows-specific window enumeration is isolated in ``WindowsAppCloser`` and
kept behind a tiny interface so the controller logic stays fully testable with a
fake closer (see ``StaticAppCloser``), matching the injectable-reader pattern
used by ``idle_service`` and ``network_service``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import time

WM_CLOSE = 0x0010
GW_OWNER = 4
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000

# Window classes that belong to the shell / desktop and must never be closed.
_SHELL_WINDOW_CLASSES = {
    "Progman",          # Program Manager (desktop)
    "WorkerW",          # desktop wallpaper host
    "Shell_TrayWnd",    # taskbar
    "Shell_SecondaryTrayWnd",
    "Button",           # start button
}

_SYSTEM_WINDOW_CLASSES = _SHELL_WINDOW_CLASSES | {
    "NotifyIconOverflowWindow",
    "CiceroUIWndFrame",
    "MSCTFIME UI",
    "IME",
    "SysShadow",
}

_SYSTEM_WINDOW_CLASS_PREFIXES = (
    "MSCTFIME",
)


def should_ignore_window_class(class_name):
    clean = str(class_name or "").strip()
    return clean in _SYSTEM_WINDOW_CLASSES or clean.startswith(_SYSTEM_WINDOW_CLASS_PREFIXES)


@dataclass(frozen=True)
class AppWindow:
    """A visible top-level application window owned by another process."""

    hwnd: int
    pid: int
    title: str


@dataclass
class CloseAppsResult:
    available: bool
    attempted: int
    closed: int
    remaining: int
    titles: list = field(default_factory=list)
    message: str = ""
    cancelled: bool = False
    remaining_titles: list = field(default_factory=list)
    requested_titles: list = field(default_factory=list)
    request_failed_titles: list = field(default_factory=list)


class StaticAppCloser:
    """Deterministic closer for tests.

    ``windows`` is the list returned by :meth:`list_app_windows`. Each call to
    :meth:`request_close` records the window and removes it from the live set so
    that polling eventually observes an empty desktop (unless ``stubborn`` pids
    are configured to ignore the close request).
    """

    def __init__(self, windows, stubborn_pids=None):
        self._initial = list(windows)
        self._live = list(windows)
        self._stubborn = set(stubborn_pids or ())
        self.close_calls = []

    def list_app_windows(self):
        return list(self._live)

    def request_close(self, window):
        self.close_calls.append(window)
        if window.pid in self._stubborn:
            return False
        self._live = [w for w in self._live if w.hwnd != window.hwnd]
        return True


class WindowsAppCloser:
    """Enumerates and politely closes real Windows application windows."""

    def __init__(self, own_pid=None):
        import os

        self._own_pid = int(own_pid if own_pid is not None else os.getpid())
        self._user32 = None

    def _load_user32(self):
        if self._user32 is not None:
            return self._user32
        import ctypes
        import ctypes.wintypes as wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.IsWindowVisible.argtypes = [wintypes.HWND]
        user32.IsWindowVisible.restype = wintypes.BOOL
        user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        user32.GetWindowTextLengthW.restype = ctypes.c_int
        user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        user32.GetWindowTextW.restype = ctypes.c_int
        user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        user32.GetClassNameW.restype = ctypes.c_int
        user32.GetWindow.argtypes = [wintypes.HWND, ctypes.c_uint]
        user32.GetWindow.restype = wintypes.HWND
        user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.GetWindowLongW.restype = ctypes.c_long
        user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        user32.PostMessageW.argtypes = [wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM]
        user32.PostMessageW.restype = wintypes.BOOL
        self._ctypes = ctypes
        self._wintypes = wintypes
        self._user32 = user32
        return user32

    def list_app_windows(self):
        try:
            user32 = self._load_user32()
        except Exception:
            return []
        ctypes = self._ctypes
        wintypes = self._wintypes

        results = []
        enum_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def _callback(hwnd, _lparam):
            try:
                if not user32.IsWindowVisible(hwnd):
                    return True
                # Only top-level, non-owned windows that appear on the taskbar.
                ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                owner = user32.GetWindow(hwnd, GW_OWNER)
                is_tool = bool(ex_style & WS_EX_TOOLWINDOW)
                is_app = bool(ex_style & WS_EX_APPWINDOW)
                if owner and not is_app:
                    return True
                if is_tool and not is_app:
                    return True

                length = user32.GetWindowTextLengthW(hwnd)
                if length <= 0:
                    return True
                buffer = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buffer, length + 1)
                title = buffer.value.strip()
                if not title:
                    return True

                class_buffer = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, class_buffer, 256)
                if should_ignore_window_class(class_buffer.value):
                    return True

                pid = wintypes.DWORD(0)
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value == 0 or pid.value == self._own_pid:
                    return True

                results.append(AppWindow(hwnd=int(hwnd), pid=int(pid.value), title=title))
            except Exception:
                # A single bad window must never abort the whole enumeration.
                return True
            return True

        try:
            user32.EnumWindows(enum_proc(_callback), 0)
        except Exception:
            return []
        return results

    def request_close(self, window):
        try:
            user32 = self._load_user32()
            return bool(user32.PostMessageW(window.hwnd, WM_CLOSE, 0, 0))
        except Exception:
            return False


def _coerce_nonnegative_int(value, fallback=0):
    try:
        return max(0, int(value))
    except (TypeError, ValueError, OverflowError):
        return fallback


def _coerce_poll_interval(value, fallback=0.5):
    try:
        interval = float(value)
    except (TypeError, ValueError, OverflowError):
        return fallback
    if not math.isfinite(interval):
        return fallback
    return max(0.05, interval)


def close_user_apps(closer, timeout_seconds=20, poll_interval=0.5,
                    sleep_func=time.sleep, time_func=time.monotonic,
                    should_stop=None):
    """Ask every listed application window to close and wait for them to exit.

    Returns a :class:`CloseAppsResult` summarising how many apps were asked to
    close and how many were still running when the timeout elapsed. Force-kill
    is intentionally never used.
    """
    if closer is None:
        return CloseAppsResult(available=False, attempted=0, closed=0, remaining=0,
                               message="关闭应用服务不可用")

    try:
        windows = list(closer.list_app_windows())
    except Exception as exc:
        return CloseAppsResult(available=False, attempted=0, closed=0, remaining=0,
                               message=f"关闭应用服务不可用：{exc}")
    titles = [w.title for w in windows]
    target_pids = {w.pid for w in windows}
    initial_count = len(windows)

    if initial_count == 0:
        return CloseAppsResult(available=True, attempted=0, closed=0, remaining=0,
                               titles=[], message="没有需要关闭的应用")

    attempted = 0
    requested_titles = []
    request_failed_titles = []
    for window in windows:
        try:
            requested = closer.request_close(window)
        except Exception:
            requested = False
        if requested:
            attempted += 1
            requested_titles.append(window.title)
        else:
            request_failed_titles.append(window.title)

    def _remaining_windows():
        try:
            return [w for w in closer.list_app_windows() if w.pid in target_pids]
        except Exception:
            return []

    timeout_seconds = _coerce_nonnegative_int(timeout_seconds)
    poll_interval = _coerce_poll_interval(poll_interval)
    deadline = time_func() + timeout_seconds
    remaining_windows = _remaining_windows()
    remaining = len(remaining_windows)
    cancelled = False
    while remaining > 0 and time_func() < deadline:
        if should_stop is not None and should_stop():
            cancelled = True
            break
        sleep_for = min(poll_interval, max(0, deadline - time_func()))
        if sleep_for <= 0:
            break
        sleep_func(sleep_for)
        remaining_windows = _remaining_windows()
        remaining = len(remaining_windows)

    closed = max(0, initial_count - remaining)
    remaining_titles = [w.title for w in remaining_windows]
    if cancelled and remaining > 0:
        message = f"已请求关闭 {attempted} 个应用，已跳过等待，仍有 {remaining} 个未退出"
    elif remaining == 0:
        message = f"已请求关闭 {attempted} 个应用，全部已退出"
    else:
        message = f"已请求关闭 {attempted} 个应用，仍有 {remaining} 个未在 {timeout_seconds} 秒内退出"
    return CloseAppsResult(
        available=True,
        attempted=attempted,
        closed=closed,
        remaining=remaining,
        cancelled=cancelled,
        remaining_titles=remaining_titles,
        requested_titles=requested_titles,
        request_failed_titles=request_failed_titles,
        titles=titles,
        message=message,
    )
