"""调用 Windows 自带的 shutdown.exe 排定或取消关机。

倒计时交给系统而不是自己 sleep：程序被关掉、崩溃、甚至注销，
到点照样关机；取消用 /a 撤销。
"""

import math
import subprocess

# shutdown /a 在没有待执行关机时返回 1116，属于「本来就没排」，不算失败。
_NO_PENDING_SHUTDOWN = 1116


def _run(args):
    completed = subprocess.run(
        args,
        capture_output=True,
        text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return completed.returncode, (completed.stderr or "").strip()


def schedule_shutdown(delay_seconds, runner=_run):
    """排定 delay_seconds 秒后关机，返回 (是否成功, 提示文案)。"""
    delay = max(0, math.ceil(delay_seconds))
    returncode, stderr = runner(["shutdown.exe", "/s", "/t", str(delay)])
    if returncode == 0:
        return True, ""
    return False, stderr or f"shutdown.exe 返回 {returncode}"


def cancel_shutdown(runner=_run):
    """取消已排定的关机，返回 (是否成功, 提示文案)。"""
    returncode, stderr = runner(["shutdown.exe", "/a"])
    if returncode in (0, _NO_PENDING_SHUTDOWN):
        return True, ""
    return False, stderr or f"shutdown.exe 返回 {returncode}"
