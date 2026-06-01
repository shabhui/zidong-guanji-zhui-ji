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
    kernel32.CloseHandle(hToken)
    return True


def execute_power_action(action: str, force: bool = False):
    if action == "logoff":
        _enable_shutdown_privilege()
        ctypes.windll.user32.ExitWindowsEx(EWX_LOGOFF, 0)
        return

    if action == "lock":
        ctypes.windll.user32.LockWorkStation()
        return

    if action == "sleep":
        subprocess.run(
            ["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"],
            check=False,
        )
        return

    if action == "hibernate":
        subprocess.run(
            ["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "0", "0"],
            check=False,
        )
        return

    flags_map = {"shutdown": EWX_SHUTDOWN, "restart": EWX_REBOOT}
    flags = flags_map.get(action, 0)
    if force and action in ("shutdown", "restart"):
        flags |= EWX_FORCE | EWX_FORCEIFHUNG
    if flags:
        _enable_shutdown_privilege()
        ctypes.windll.user32.ExitWindowsEx(flags, 0)
