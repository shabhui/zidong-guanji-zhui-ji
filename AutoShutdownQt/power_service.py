import subprocess
import ctypes
import ctypes.wintypes

TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_QUERY = 0x0008
SE_SHUTDOWN_NAME = "SeShutdownPrivilege"
SE_PRIVILEGE_ENABLED = 0x00000002
EWX_SHUTDOWN = 0x00000001
EWX_REBOOT = 0x00000002
EWX_LOGOFF = 0x00000000
EWX_FORCE = 0x00000004
EWX_FORCEIFHUNG = 0x00000010


def _enable_shutdown_privilege():
    advapi32 = ctypes.windll.advapi32
    kernel32 = ctypes.windll.kernel32
    hToken = ctypes.wintypes.HANDLE()
    if not advapi32.OpenProcessToken(
        kernel32.GetCurrentProcess(),
        TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY,
        ctypes.byref(hToken),
    ):
        return False
    luid = ctypes.wintypes.LARGE_INTEGER()
    if not advapi32.LookupPrivilegeValueW(None, SE_SHUTDOWN_NAME, ctypes.byref(luid)):
        kernel32.CloseHandle(hToken)
        return False
    tp = (luid, SE_PRIVILEGE_ENABLED)
    advapi32.AdjustTokenPrivileges(hToken, False, ctypes.byref(tp), 0, None, None)
    success = kernel32.GetLastError() == 0
    kernel32.CloseHandle(hToken)
    return success


def execute_power_action(action: str, force: bool = False):
    if action == "logoff":
        _enable_shutdown_privilege()
        return bool(ctypes.windll.user32.ExitWindowsEx(EWX_LOGOFF, 0))

    if action == "lock":
        return bool(ctypes.windll.user32.LockWorkStation())

    if action == "sleep":
        completed = subprocess.run(
            ["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"],
            check=False,
        )
        return completed.returncode == 0

    if action == "hibernate":
        completed = subprocess.run(
            ["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "0", "0"],
            check=False,
        )
        return completed.returncode == 0

    if action in ("shutdown", "restart"):
        args = ["shutdown.exe", "/s" if action == "shutdown" else "/r", "/t", "0"]
        if force:
            args.append("/f")
        completed = subprocess.run(args, check=False)
        return completed.returncode == 0

    return False
