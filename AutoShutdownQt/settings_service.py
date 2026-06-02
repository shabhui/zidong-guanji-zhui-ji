import json
import os
from pathlib import Path


DEFAULT_SETTINGS = {
    "dryRun": True,
    "forceClose": False,
    "selectedAction": "shutdown",
    "scriptEnabled": False,
    "scriptPath": "",
    "scriptTimeoutSeconds": 10,
    "processName": "",
    "processPollSeconds": 5,
    "networkDownloadThresholdKbps": 10.0,
    "networkUploadThresholdKbps": 10.0,
    "networkIdleSeconds": 60,
    "networkPollSeconds": 3,
}


def default_settings():
    return dict(DEFAULT_SETTINGS)


def settings_path():
    base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / "AutoShutdownQt" / "settings.json"
    return Path.home() / ".autoshutdownqt" / "settings.json"


def log_export_path():
    base = os.environ.get("USERPROFILE")
    if base:
        return Path(base) / "Documents" / "AutoShutdownQt-logs.txt"
    return Path.home() / "AutoShutdownQt-logs.txt"


def load_settings(path=None):
    target = Path(path) if path is not None else settings_path()
    settings = default_settings()
    try:
        loaded = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return settings
    if not isinstance(loaded, dict):
        return settings
    settings.update(loaded)
    return settings


def save_settings(settings, path=None):
    target = Path(path) if path is not None else settings_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    merged = default_settings()
    if isinstance(settings, dict):
        merged.update(settings)
    target.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target
