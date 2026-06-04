import json
import tempfile
import unittest
from pathlib import Path

import sys
ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
sys.path.insert(0, str(APP_DIR))

from settings_service import default_settings
from history_service import HistoryEvent, append_history_event, clear_history, export_history_json, history_rows_json


class HistoryServiceTest(unittest.TestCase):
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

    def test_clear_and_export_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = {"taskHistory": [], "taskHistoryLimit": 10}
            append_history_event(settings, HistoryEvent("2026-06-04T10:00:00", "created", "shutdown", "countdown", "dry-run", "a", "first"))
            target = Path(tmp) / "history.json"

            exported = export_history_json(settings, target)
            clear_history(settings)

            self.assertEqual(exported, target)
            self.assertEqual(settings["taskHistory"], [])
            self.assertEqual(json.loads(target.read_text(encoding="utf-8"))[0]["message"], "first")


if __name__ == "__main__":
    unittest.main()
