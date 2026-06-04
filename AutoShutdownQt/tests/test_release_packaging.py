import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
MAIN_PY = APP_DIR / "main.py"
SPEC = APP_DIR / "AutoShutdownQt-2.4.spec"
PACKAGE_SCRIPT = APP_DIR / "package_release.py"
README = ROOT / "README.md"
sys.path.insert(0, str(APP_DIR))

import package_release


class ReleasePackagingTest(unittest.TestCase):
    def _valid_manifest(self, archive_name="AutoShutdownQt-2.4.zip", bundle="AutoShutdownQt-2.4"):
        return {
            "app": "AutoShutdownQt",
            "version": "2.4",
            "bundle": bundle,
            "executable": "AutoShutdownQt.exe",
            "archive": archive_name,
            "checks": {
                "executablePresent": True,
                "mainQmlPresent": True,
                "taskSchedulerIncluded": True,
                "bundledMusicPresent": True,
            },
            "safetyNotes": [
                "Dry-run is enabled by default.",
                "Live mode can execute real Windows power actions.",
            ],
        }

    def _write_valid_archive(self, archive_path, manifest=None):
        manifest = self._valid_manifest(archive_path.name) if manifest is None else manifest
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("AutoShutdownQt-2.4/AutoShutdownQt.exe", "exe")
            archive.writestr("AutoShutdownQt-2.4/_internal/qml/Main.qml", "qml")
            archive.writestr("AutoShutdownQt-2.4/release-manifest.json", json.dumps(manifest))
            archive.writestr("AutoShutdownQt-2.4/demo.mp3", b"mp3")
    def test_main_declares_final_2_0_version(self):
        main = MAIN_PY.read_text(encoding="utf-8")
        self.assertIn('app.setApplicationVersion("2.4")', main)
        self.assertNotIn("2.4-preview", main)

    def test_pyinstaller_spec_includes_qml_and_runtime_modules(self):
        spec = SPEC.read_text(encoding="utf-8")
        self.assertIn("AutoShutdownQt-2.4", spec)
        self.assertIn("main.py", spec)
        self.assertIn("qml", spec)
        self.assertIn("controller", spec)
        self.assertIn("settings_service", spec)
        self.assertIn("network_service", spec)
        self.assertIn("power_service", spec)
        self.assertIn("script_service", spec)
        self.assertIn("music_service", spec)
        self.assertIn("PySide6.QtQml", spec)
        self.assertIn("PySide6.QtQuick", spec)
        self.assertIn("PySide6.QtQuickControls2", spec)
        self.assertIn("PySide6.QtMultimedia", spec)

    def test_pyinstaller_hiddenimports_use_module_names_not_py_files(self):
        spec = SPEC.read_text(encoding="utf-8")
        self.assertNotIn('"controller.py",', spec)
        self.assertNotIn('"settings_service.py",', spec)
        self.assertNotIn('"network_service.py",', spec)
        self.assertNotIn('"power_service.py",', spec)
        self.assertNotIn('"script_service.py",', spec)

    def test_gitignore_allows_release_spec_to_be_committed(self):
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("!AutoShutdownQt/AutoShutdownQt-2.4.spec", gitignore)

    def test_release_script_builds_versioned_zip_from_spec(self):
        script = PACKAGE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn('VERSION = "2.4"', script)
        self.assertIn('SPEC_FILE = APP_DIR / "AutoShutdownQt-2.4.spec"', script)
        self.assertIn('DIST_DIR / "AutoShutdownQt-2.4"', script)
        self.assertIn('AutoShutdownQt-2.4.zip', script)
        self.assertIn("PyInstaller", script)
        self.assertIn("zipfile", script)
        self.assertIn("validate_zip_contents", script)

    def test_release_script_copies_root_mp3_into_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = root / "dist" / "AutoShutdownQt-2.4"
            bundle.mkdir(parents=True)
            (root / "theme.mp3").write_bytes(b"mp3")

            copied = package_release.copy_bundled_music(root, bundle)

            self.assertEqual(copied, [bundle / "theme.mp3"])
            self.assertEqual((bundle / "theme.mp3").read_bytes(), b"mp3")

    def test_release_archive_validation_fails_when_music_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "AutoShutdownQt-2.4.zip"
            manifest = self._valid_manifest(archive_path.name)
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("AutoShutdownQt-2.4/AutoShutdownQt.exe", "exe")
                archive.writestr("AutoShutdownQt-2.4/_internal/qml/Main.qml", "qml")
                archive.writestr("AutoShutdownQt-2.4/release-manifest.json", json.dumps(manifest))

            with self.assertRaisesRegex(RuntimeError, "music"):
                package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_passes_when_exe_qml_music_and_matching_manifest_are_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "AutoShutdownQt-2.4.zip"
            self._write_valid_archive(archive_path)

            self.assertTrue(package_release.validate_zip_contents(archive_path))

    def test_release_archive_validation_fails_when_manifest_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "AutoShutdownQt-2.4.zip"
            self._write_valid_archive(archive_path, manifest={})

            with self.assertRaisesRegex(RuntimeError, "manifest.*version"):
                package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_fails_when_manifest_is_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "AutoShutdownQt-2.4.zip"
            manifest = self._valid_manifest(archive_path.name)
            manifest["version"] = "1.9"
            self._write_valid_archive(archive_path, manifest=manifest)

            with self.assertRaisesRegex(RuntimeError, "manifest.*version"):
                package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_fails_when_manifest_identity_fields_are_stale(self):
        stale_cases = (
            ("bundle", "AutoShutdownQt-1.9", "manifest.*bundle"),
            ("executable", "OldAutoShutdown.exe", "manifest.*executable"),
            ("archive", "old-release.zip", "manifest.*archive"),
        )
        for field, stale_value, expected_error in stale_cases:
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as tmp:
                    archive_path = Path(tmp) / "AutoShutdownQt-2.4.zip"
                    manifest = self._valid_manifest(archive_path.name)
                    manifest[field] = stale_value
                    self._write_valid_archive(archive_path, manifest=manifest)

                    with self.assertRaisesRegex(RuntimeError, expected_error):
                        package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_fails_when_manifest_checks_disagree_with_contents(self):
        stale_checks = ("executablePresent", "mainQmlPresent")
        for check_name in stale_checks:
            with self.subTest(check_name=check_name):
                with tempfile.TemporaryDirectory() as tmp:
                    archive_path = Path(tmp) / "AutoShutdownQt-2.4.zip"
                    manifest = self._valid_manifest(archive_path.name)
                    manifest["checks"][check_name] = False
                    self._write_valid_archive(archive_path, manifest=manifest)

                    with self.assertRaisesRegex(RuntimeError, f"manifest.*{check_name}"):
                        package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_fails_when_exe_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "AutoShutdownQt-2.4.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("AutoShutdownQt-2.4/_internal/qml/Main.qml", "qml")

            with self.assertRaisesRegex(RuntimeError, "AutoShutdownQt.exe"):
                package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_fails_when_qml_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "AutoShutdownQt-2.4.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("AutoShutdownQt-2.4/AutoShutdownQt.exe", "exe")
                archive.writestr("AutoShutdownQt-2.4/release-manifest.json", json.dumps(self._valid_manifest(archive_path.name)))

            with self.assertRaisesRegex(RuntimeError, "QML"):
                package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_fails_when_main_qml_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "AutoShutdownQt-2.4.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("AutoShutdownQt-2.4/AutoShutdownQt.exe", "exe")
                archive.writestr("AutoShutdownQt-2.4/_internal/qml/Theme.qml", "qml")
                archive.writestr("AutoShutdownQt-2.4/release-manifest.json", json.dumps(self._valid_manifest(archive_path.name)))

            with self.assertRaisesRegex(RuntimeError, "Main.qml"):
                package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_fails_when_manifest_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "AutoShutdownQt-2.4.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("AutoShutdownQt-2.4/AutoShutdownQt.exe", "exe")
                archive.writestr("AutoShutdownQt-2.4/_internal/qml/Main.qml", "qml")

            with self.assertRaisesRegex(RuntimeError, "release-manifest.json"):
                package_release.validate_zip_contents(archive_path)

    def test_release_manifest_records_version_and_safety_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "AutoShutdownQt-2.4"
            (bundle / "_internal" / "qml").mkdir(parents=True)
            (bundle / "AutoShutdownQt.exe").write_text("exe", encoding="utf-8")
            (bundle / "_internal" / "qml" / "Main.qml").write_text("qml", encoding="utf-8")

            manifest_path = package_release.create_release_manifest(bundle)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            self.assertEqual(manifest["version"], "2.4")
            self.assertEqual(manifest["executable"], "AutoShutdownQt.exe")
            self.assertTrue(manifest["checks"]["mainQmlPresent"])
            self.assertIn("dry-run", " ".join(manifest["safetyNotes"]).lower())

    def test_release_notes_document_portable_dry_run_and_unsigned_status(self):
        notes = (ROOT / "RELEASE_NOTES_v2.4.md").read_text(encoding="utf-8")
        self.assertIn("Dry-run", notes)
        self.assertIn("便携版", notes)
        self.assertIn("未做代码签名", notes)
        self.assertIn("dist/AutoShutdownQt-2.4.zip", notes)

    def test_readme_current_release_status_mentions_main_not_old_feature_branch(self):
        readme = README.read_text(encoding="utf-8")
        self.assertIn("main", readme)
        self.assertNotIn("v2-e5e8-reference-ui", readme)
    def test_main_declares_final_2_1_version(self):
        main = MAIN_PY.read_text(encoding="utf-8")
        self.assertIn('app.setApplicationVersion("2.4")', main)

    def test_release_script_builds_2_1_checksum_and_checklist(self):
        script = PACKAGE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn('VERSION = "2.4"', script)
        self.assertIn('AutoShutdownQt-2.4.zip', script)
        self.assertIn('SHA256SUMS.txt', script)
        self.assertIn('release-checklist-v2.4.md', script)
        self.assertIn('create_sha256sums', script)
        self.assertIn('create_release_checklist', script)

    def test_checksum_file_contains_archive_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "AutoShutdownQt-2.4.zip"
            archive_path.write_bytes(b"demo")

            sums = package_release.create_sha256sums(archive_path, Path(tmp) / "SHA256SUMS.txt")
            content = sums.read_text(encoding="utf-8")

            self.assertIn("AutoShutdownQt-2.4.zip", content)
            self.assertRegex(content, r"^[0-9a-f]{64}  AutoShutdownQt-2.4.zip")

    def test_release_checklist_mentions_dry_run_and_no_real_power_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            checklist = package_release.create_release_checklist(Path(tmp) / "release-checklist-v2.4.md")
            content = checklist.read_text(encoding="utf-8")

            self.assertIn("Dry-run", content)
            self.assertIn("Do not execute real shutdown", content)
            self.assertIn("SHA256SUMS.txt", content)
    def test_main_declares_final_2_3_version(self):
        main = MAIN_PY.read_text(encoding="utf-8")
        self.assertIn('app.setApplicationVersion("2.4")', main)

    def test_release_script_builds_2_3_artifacts(self):
        script = PACKAGE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn('VERSION = "2.4"', script)
        self.assertIn('AutoShutdownQt-2.4.spec', script)
        self.assertIn('AutoShutdownQt-2.4.zip', script)
        self.assertIn('release-checklist-v2.4.md', script)

    def test_release_checklist_mentions_command_center_and_recent_activity(self):
        with tempfile.TemporaryDirectory() as tmp:
            checklist = package_release.create_release_checklist(Path(tmp) / "release-checklist-v2.4.md")
            content = checklist.read_text(encoding="utf-8")

            self.assertIn("Command Center", content)
            self.assertIn("Queue health", content)
            self.assertIn("Recent activity", content)

    def test_release_notes_document_2_3_command_center_patch(self):
        notes = (ROOT / "RELEASE_NOTES_v2.4.md").read_text(encoding="utf-8")
        self.assertIn("2.4", notes)
        self.assertIn("command center", notes.lower())
        self.assertIn("queue", notes.lower())
        self.assertIn("tray", notes.lower())
        self.assertIn("SHA256SUMS.txt", notes)

    def test_readme_mentions_2_3_download_and_checksum(self):
        readme = README.read_text(encoding="utf-8")
        self.assertIn("AutoShutdownQt 2.4", readme)
        self.assertIn("AutoShutdownQt-2.4.zip", readme)
        self.assertIn("SHA256SUMS.txt", readme)


if __name__ == "__main__":
    unittest.main()
