import json
import shutil
import unittest
from pathlib import Path

import sys
ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
sys.path.insert(0, str(APP_DIR))

from settings_service import default_settings
from history_service import HistoryEvent, append_history_event, clear_history, export_history_json, history_rows_json


class HistoryServiceTest(unittest.TestCase):
    def _workspace_scratch(self, name):
        target = ROOT / "test-tmp" / name
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        target.mkdir(parents=True, exist_ok=True)
        self.addCleanup(lambda: shutil.rmtree(target, ignore_errors=True))
        return target

    def test_default_settings_include_history_retention(self):
        settings = default_settings()

        self.assertEqual(settings["taskHistory"], [])
        self.assertEqual(settings["taskHistoryLimit"], 500)

    def test_append_history_event_trims_old_entries_to_limit(self):
        settings = {"taskHistory": [], "taskHistoryLimit": 2}

        append_history_event(settings, HistoryEvent("2026-06-04T10:00:00", "created", "shutdown", "countdown", "dry-run", "a", "first"))
        append_history_event(settings, HistoryEvent("2026-06-04T10:01:00", "snoozed", "shutdown", "countdown", "dry-run", "b", "second"))
        append_history_event(settings, HistoryEvent("2026-06-04T10:02:00", "cancelled", "sleep", "fixed-time", "dry-run", "c", "third"))

        self.assertEqual([row["message"] for row in settings["taskHistory"]], ["second", "third"])

    def test_history_rows_json_returns_newest_first(self):
        settings = {"taskHistory": [], "taskHistoryLimit": 10}
        append_history_event(settings, HistoryEvent("2026-06-04T10:00:00", "created", "shutdown", "countdown", "dry-run", "a", "first"))
        append_history_event(settings, HistoryEvent("2026-06-04T10:01:00", "cancelled", "sleep", "fixed-time", "dry-run", "b", "second"))

        rows = json.loads(history_rows_json(settings))

        self.assertEqual([row["message"] for row in rows], ["second", "first"])

    def test_history_rows_json_includes_readable_chinese_labels_for_ui(self):
        settings = {"taskHistory": [], "taskHistoryLimit": 10}
        append_history_event(
            settings,
            HistoryEvent(
                "2026-06-04T10:00:00",
                "cancelled",
                "sleep",
                "fixed-time",
                "live",
                "task-b",
                "固定时间任务：已取消当前任务",
            ),
        )

        row = json.loads(history_rows_json(settings))[0]

        self.assertEqual(row.get("eventLabel"), "已取消")
        self.assertEqual(row.get("actionLabel"), "睡眠")
        self.assertEqual(row.get("sourceLabel"), "固定时间")
        self.assertEqual(row.get("modeLabel"), "真实执行")

    def test_clear_and_export_history(self):
        root = self._workspace_scratch("history-export")
        settings = {"taskHistory": [], "taskHistoryLimit": 10}
        append_history_event(settings, HistoryEvent("2026-06-04T10:00:00", "created", "shutdown", "countdown", "dry-run", "a", "first"))
        target = root / "history.json"

        exported = export_history_json(settings, target)
        clear_history(settings)

        self.assertEqual(exported, target)
        self.assertEqual(settings["taskHistory"], [])
        self.assertEqual(json.loads(target.read_text(encoding="utf-8"))[0]["message"], "first")

    def test_export_history_json_includes_readable_chinese_labels(self):
        root = self._workspace_scratch("history-export-labels")
        settings = {"taskHistory": [], "taskHistoryLimit": 10}
        append_history_event(
            settings,
            HistoryEvent(
                "2026-06-04T10:00:00",
                "created",
                "shutdown",
                "active-countdown",
                "dry-run",
                "task-a",
                "手动倒计时：已加入任务",
            ),
        )
        target = root / "history.json"

        export_history_json(settings, target)
        row = json.loads(target.read_text(encoding="utf-8"))[0]

        self.assertEqual(row["event"], "created")
        self.assertEqual(row.get("eventLabel"), "已创建")
        self.assertEqual(row.get("actionLabel"), "关机")
        self.assertEqual(row.get("sourceLabel"), "手动倒计时")
        self.assertEqual(row.get("modeLabel"), "安全验证")


if __name__ == "__main__":
    unittest.main()
