import sys
from pathlib import Path
import tempfile
import unittest

from PySide6.QtCore import QCoreApplication

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
sys.path.insert(0, str(APP_DIR))

from controller import AppController
from network_service import NetworkSample, compute_speed
from settings_service import default_settings, load_settings, save_settings


class FakeNetworkReader:
    def __init__(self, samples):
        self.samples = list(samples)

    def sample(self):
        if not self.samples:
            return NetworkSample(False, message="no more samples")
        return self.samples.pop(0)


class PracticalEnhancementsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_settings_round_trip_merges_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            data = default_settings()
            data.update({
                "dryRun": False,
                "selectedAction": "sleep",
                "scriptPath": "C:/demo.bat",
                "networkDownloadThresholdKbps": 12.5,
            })

            save_settings(data, path)
            loaded = load_settings(path)

            self.assertFalse(loaded["dryRun"])
            self.assertEqual(loaded["selectedAction"], "sleep")
            self.assertEqual(loaded["scriptPath"], "C:/demo.bat")
            self.assertEqual(loaded["networkDownloadThresholdKbps"], 12.5)
            self.assertIn("networkIdleSeconds", loaded)

    def test_controller_saves_settings_when_persisted_properties_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            controller = AppController(settings_path=path)

            controller.selectedAction = "sleep"
            controller.scriptEnabled = True
            controller.scriptPath = "C:/scripts/demo.bat"
            controller.networkDownloadThresholdKbps = 8.0

            loaded = load_settings(path)
            self.assertEqual(loaded["selectedAction"], "sleep")
            self.assertTrue(loaded["scriptEnabled"])
            self.assertEqual(loaded["scriptPath"], "C:/scripts/demo.bat")
            self.assertEqual(loaded["networkDownloadThresholdKbps"], 8.0)

    def test_controller_falls_back_from_non_finite_persisted_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            path.write_text(
                """
                {
                  "scriptTimeoutSeconds": Infinity,
                  "processPollSeconds": Infinity,
                  "networkDownloadThresholdKbps": NaN,
                  "networkUploadThresholdKbps": Infinity,
                  "networkIdleSeconds": Infinity,
                  "networkPollSeconds": Infinity
                }
                """,
                encoding="utf-8",
            )

            controller = AppController(settings_path=path)

            self.assertEqual(controller.scriptTimeoutSeconds, 10)
            self.assertEqual(controller.processPollSeconds, 5)
            self.assertEqual(controller.networkDownloadThresholdKbps, 10.0)
            self.assertEqual(controller.networkUploadThresholdKbps, 10.0)
            self.assertEqual(controller.networkIdleSeconds, 60)
            self.assertEqual(controller.networkPollSeconds, 3)

    def test_compute_speed_reports_kbps_delta(self):
        previous = NetworkSample(True, received_bytes=1024, sent_bytes=2048, monotonic_seconds=10.0)
        current = NetworkSample(True, received_bytes=3072, sent_bytes=4096, monotonic_seconds=12.0)

        speed = compute_speed(previous, current)

        self.assertTrue(speed.available)
        self.assertAlmostEqual(speed.download_kbps, 1.0)
        self.assertAlmostEqual(speed.upload_kbps, 1.0)

    def test_compute_speed_treats_counter_reset_as_unavailable(self):
        previous = NetworkSample(True, received_bytes=4096, sent_bytes=4096, monotonic_seconds=10.0)
        current = NetworkSample(True, received_bytes=1024, sent_bytes=8192, monotonic_seconds=11.0)

        speed = compute_speed(previous, current)

        self.assertFalse(speed.available)
        self.assertIn("reset", speed.message)

    def test_network_idle_trigger_fires_after_sustained_low_speed(self):
        samples = [
            NetworkSample(True, received_bytes=1000, sent_bytes=1000, monotonic_seconds=1.0),
            NetworkSample(True, received_bytes=1100, sent_bytes=1100, monotonic_seconds=2.0),
            NetworkSample(True, received_bytes=1200, sent_bytes=1200, monotonic_seconds=3.0),
        ]
        controller = AppController(network_reader=FakeNetworkReader(samples))
        controller.networkDownloadThresholdKbps = 1.0
        controller.networkUploadThresholdKbps = 1.0
        controller.networkIdleSeconds = 2
        controller.networkPollSeconds = 1

        controller.startNetworkTrigger()
        controller._poll_network_trigger()
        controller._poll_network_trigger()

        self.assertFalse(controller.networkTriggerActive)
        self.assertIn("网络闲置触发", controller.logText)
        self.assertIn("[dryRun] Would execute", controller.logText)

    def test_network_busy_sample_resets_idle_accumulation(self):
        samples = [
            NetworkSample(True, received_bytes=0, sent_bytes=0, monotonic_seconds=1.0),
            NetworkSample(True, received_bytes=100, sent_bytes=100, monotonic_seconds=2.0),
            NetworkSample(True, received_bytes=10_000, sent_bytes=100, monotonic_seconds=3.0),
        ]
        controller = AppController(network_reader=FakeNetworkReader(samples))
        controller.networkDownloadThresholdKbps = 1.0
        controller.networkUploadThresholdKbps = 1.0
        controller.networkIdleSeconds = 2

        controller.startNetworkTrigger()
        controller._poll_network_trigger()
        controller._poll_network_trigger()

        self.assertTrue(controller.networkTriggerActive)
        self.assertIn("0/2 秒", controller.networkTriggerStatus)

    def test_network_unavailable_logs_and_stops_without_triggering(self):
        controller = AppController(network_reader=FakeNetworkReader([
            NetworkSample(False, message="network unavailable"),
        ]))

        controller.startNetworkTrigger()

        self.assertFalse(controller.networkTriggerActive)
        self.assertIn("network unavailable", controller.networkTriggerStatus)
        self.assertNotIn("[dryRun] Would execute", controller.logText)

    def test_clear_and_export_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            controller = AppController(log_export_path=Path(tmp) / "logs.txt")
            controller.applyTaskTemplate("shutdown_15")

            controller.exportLogs()
            exported = Path(tmp) / "logs.txt"
            self.assertTrue(exported.exists())
            self.assertIn("15 分钟后关机", exported.read_text(encoding="utf-8"))

            controller.clearLogs()
            self.assertNotIn("15 分钟后关机", controller.logText)
            self.assertIn("日志已清空", controller.logText)

    def test_script_path_validation_and_open_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "demo.bat"
            script.write_text("echo demo", encoding="utf-8")
            opened = []
            controller = AppController(open_folder=lambda path: opened.append(Path(path)))
            controller.scriptPath = str(script)

            controller.validateScriptPath()
            controller.openScriptFolder()

            self.assertIn("脚本路径有效", controller.logText)
            self.assertEqual(opened, [script.parent])


if __name__ == "__main__":
    unittest.main()
