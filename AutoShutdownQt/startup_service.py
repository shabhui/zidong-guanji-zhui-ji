import sys
from pathlib import Path

APP_NAME = "定时关机助手"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def startup_command(executable):
    return f'"{Path(executable).as_posix()}"'


class WindowsRunRegistry:
    def set_value(self, name, value):
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)

    def delete_value(self, name):
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, name)
        except FileNotFoundError:
            pass

    def get_value(self, name):
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_QUERY_VALUE) as key:
                value, _ = winreg.QueryValueEx(key, name)
                return value
        except FileNotFoundError:
            return None


class StartupService:
    def __init__(self, registry=None, executable=None, name=APP_NAME):
        self._registry = registry or WindowsRunRegistry()
        self._executable = Path(executable) if executable is not None else Path(sys.executable)
        self._name = name

    def is_enabled(self):
        return self._registry.get_value(self._name) == startup_command(self._executable)

    def set_enabled(self, enabled):
        if enabled:
            self._registry.set_value(self._name, startup_command(self._executable))
        else:
            self._registry.delete_value(self._name)
        return self.is_enabled() == bool(enabled)
