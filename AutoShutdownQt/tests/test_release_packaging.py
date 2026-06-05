import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
MAIN_PY = APP_DIR / "main.py"
SPEC = APP_DIR / "AutoShutdownQt-3.1.spec"
INNO_SCRIPT = APP_DIR / "AutoShutdownQt-3.1.iss"
PACKAGE_SCRIPT = APP_DIR / "package_release.py"
README = ROOT / "README.md"
sys.path.insert(0, str(APP_DIR))

import package_release


class ReleasePackagingTest(unittest.TestCase):
    def _valid_manifest(self, archive_name="定时关机助手-3.1.zip", bundle="定时关机助手-3.1"):
        return {
            "app": "定时关机助手",
            "version": "3.1",
            "bundle": bundle,
            "executable": "定时关机助手.exe",
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
            archive.writestr("定时关机助手-3.1/定时关机助手.exe", "exe")
            archive.writestr("定时关机助手-3.1/_internal/qml/Main.qml", "qml")
            archive.writestr("定时关机助手-3.1/release-manifest.json", json.dumps(manifest))
            archive.writestr("定时关机助手-3.1/demo.mp3", b"mp3")
    def test_main_declares_final_2_5_version(self):
        main = MAIN_PY.read_text(encoding="utf-8")
        self.assertIn('app.setApplicationVersion("3.1")', main)
        self.assertNotIn("3.0-preview", main)

    def test_pyinstaller_spec_includes_qml_and_runtime_modules(self):
        spec = SPEC.read_text(encoding="utf-8")
        self.assertIn("定时关机助手-3.1", spec)
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
        self.assertIn("app_icon.png", spec)
        self.assertIn("app_icon.ico", spec)
        self.assertIn("icon=", spec)

    def test_pyinstaller_hiddenimports_use_module_names_not_py_files(self):
        spec = SPEC.read_text(encoding="utf-8")
        self.assertNotIn('"controller.py",', spec)
        self.assertNotIn('"settings_service.py",', spec)
        self.assertNotIn('"network_service.py",', spec)
        self.assertNotIn('"power_service.py",', spec)
        self.assertNotIn('"script_service.py",', spec)

    def test_gitignore_allows_release_spec_to_be_committed(self):
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("!AutoShutdownQt/AutoShutdownQt-3.1.spec", gitignore)

    def test_release_script_builds_versioned_zip_from_spec(self):
        script = PACKAGE_SCRIPT.read_text(encoding="utf-8")
        self.assertEqual(package_release.VERSION, "3.1")
        self.assertEqual(package_release.SPEC_FILE.name, "AutoShutdownQt-3.1.spec")
        self.assertEqual(package_release.APP_BUNDLE_DIR.name, "定时关机助手-3.1")
        self.assertEqual(package_release.ZIP_PATH.name, "定时关机助手-3.1.zip")
        self.assertIn("PyInstaller", script)
        self.assertIn("zipfile", script)
        self.assertIn("validate_zip_contents", script)

    def test_release_script_copies_root_mp3_into_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = root / "dist" / "定时关机助手-3.1"
            bundle.mkdir(parents=True)
            (root / "theme.mp3").write_bytes(b"mp3")

            copied = package_release.copy_bundled_music(root, bundle)

            self.assertEqual(copied, [bundle / "theme.mp3"])
            self.assertEqual((bundle / "theme.mp3").read_bytes(), b"mp3")

    def test_release_script_prunes_unused_qt_payload_after_pyinstaller(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "定时关机助手-3.1"
            keep_file = bundle / "_internal" / "PySide6" / "Qt6Quick.dll"
            webengine_file = bundle / "_internal" / "PySide6" / "Qt6WebEngineCore.dll"
            virtual_keyboard_file = bundle / "_internal" / "PySide6" / "qml" / "QtQuick" / "VirtualKeyboard" / "qtvkbplugin.dll"
            virtual_keyboard_runtime_file = bundle / "_internal" / "PySide6" / "Qt6VirtualKeyboard.dll"
            quick3d_file = bundle / "_internal" / "PySide6" / "qml" / "QtQuick3D" / "qtquick3dplugin.dll"
            quick3d_runtime_file = bundle / "_internal" / "PySide6" / "Qt6Quick3DRuntimeRender.dll"
            music_file = bundle / "theme.mp3"
            for path in (keep_file, webengine_file, virtual_keyboard_file, virtual_keyboard_runtime_file, quick3d_file, quick3d_runtime_file, music_file):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"payload")

            removed = package_release.prune_unused_qt_payload(bundle)

            self.assertFalse(webengine_file.exists())
            self.assertFalse(virtual_keyboard_file.exists())
            self.assertFalse(virtual_keyboard_runtime_file.exists())
            self.assertFalse(quick3d_file.exists())
            self.assertFalse(quick3d_runtime_file.exists())
            self.assertTrue(keep_file.exists())
            self.assertTrue(music_file.exists())
            self.assertEqual(removed, 5)

    def test_release_archive_validation_rejects_pruned_qt_payload_regressions(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "定时关机助手-3.1.zip"
            self._write_valid_archive(archive_path)
            with zipfile.ZipFile(archive_path, "a") as archive:
                archive.writestr("定时关机助手-3.1/_internal/PySide6/Qt6WebEngineCore.dll", b"web")

            with self.assertRaisesRegex(RuntimeError, "unused Qt payload"):
                package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_passes_with_required_qt_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "定时关机助手-3.1.zip"
            self._write_valid_archive(archive_path)
            with zipfile.ZipFile(archive_path, "a") as archive:
                archive.writestr("定时关机助手-3.1/_internal/PySide6/Qt6Quick.dll", b"quick")
                archive.writestr("定时关机助手-3.1/_internal/PySide6/qml/QtQuick/Controls/qmldir", b"controls")

            self.assertTrue(package_release.validate_zip_contents(archive_path))

    def test_release_archive_validation_fails_when_music_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "定时关机助手-3.1.zip"
            manifest = self._valid_manifest(archive_path.name)
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("定时关机助手-3.1/定时关机助手.exe", "exe")
                archive.writestr("定时关机助手-3.1/_internal/qml/Main.qml", "qml")
                archive.writestr("定时关机助手-3.1/release-manifest.json", json.dumps(manifest))

            with self.assertRaisesRegex(RuntimeError, "music"):
                package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_passes_when_exe_qml_music_and_matching_manifest_are_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "定时关机助手-3.1.zip"
            self._write_valid_archive(archive_path)

            self.assertTrue(package_release.validate_zip_contents(archive_path))

    def test_release_archive_validation_fails_when_manifest_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "定时关机助手-3.1.zip"
            self._write_valid_archive(archive_path, manifest={})

            with self.assertRaisesRegex(RuntimeError, "manifest.*version"):
                package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_fails_when_manifest_is_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "定时关机助手-3.1.zip"
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
                    archive_path = Path(tmp) / "定时关机助手-3.1.zip"
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
                    archive_path = Path(tmp) / "定时关机助手-3.1.zip"
                    manifest = self._valid_manifest(archive_path.name)
                    manifest["checks"][check_name] = False
                    self._write_valid_archive(archive_path, manifest=manifest)

                    with self.assertRaisesRegex(RuntimeError, f"manifest.*{check_name}"):
                        package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_fails_when_exe_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "定时关机助手-3.1.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("定时关机助手-3.1/_internal/qml/Main.qml", "qml")

            with self.assertRaisesRegex(RuntimeError, "定时关机助手.exe"):
                package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_fails_when_qml_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "定时关机助手-3.1.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("定时关机助手-3.1/定时关机助手.exe", "exe")
                archive.writestr("定时关机助手-3.1/release-manifest.json", json.dumps(self._valid_manifest(archive_path.name)))

            with self.assertRaisesRegex(RuntimeError, "QML"):
                package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_fails_when_main_qml_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "定时关机助手-3.1.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("定时关机助手-3.1/定时关机助手.exe", "exe")
                archive.writestr("定时关机助手-3.1/_internal/qml/Theme.qml", "qml")
                archive.writestr("定时关机助手-3.1/release-manifest.json", json.dumps(self._valid_manifest(archive_path.name)))

            with self.assertRaisesRegex(RuntimeError, "Main.qml"):
                package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_fails_when_manifest_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "定时关机助手-3.1.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("定时关机助手-3.1/定时关机助手.exe", "exe")
                archive.writestr("定时关机助手-3.1/_internal/qml/Main.qml", "qml")

            with self.assertRaisesRegex(RuntimeError, "release-manifest.json"):
                package_release.validate_zip_contents(archive_path)

    def test_release_manifest_records_version_and_safety_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "定时关机助手-3.1"
            (bundle / "_internal" / "qml").mkdir(parents=True)
            (bundle / "定时关机助手.exe").write_text("exe", encoding="utf-8")
            (bundle / "_internal" / "qml" / "Main.qml").write_text("qml", encoding="utf-8")

            manifest_path = package_release.create_release_manifest(bundle)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            self.assertEqual(manifest["version"], "3.1")
            self.assertEqual(manifest["executable"], "定时关机助手.exe")
            self.assertTrue(manifest["checks"]["mainQmlPresent"])
            self.assertIn("dry-run", " ".join(manifest["safetyNotes"]).lower())

    def test_release_notes_document_portable_dry_run_and_unsigned_status(self):
        notes = (ROOT / "RELEASE_NOTES_v3.1.md").read_text(encoding="utf-8")
        self.assertIn("Dry-run", notes)
        self.assertIn("便携版", notes)
        self.assertIn("未做代码签名", notes)
        self.assertIn("dist/定时关机助手-3.1.zip", notes)

    def test_readme_current_release_status_mentions_main_not_old_feature_branch(self):
        readme = README.read_text(encoding="utf-8")
        self.assertIn("main", readme)
        self.assertNotIn("v2-e5e8-reference-ui", readme)
    def test_main_declares_final_2_1_version(self):
        main = MAIN_PY.read_text(encoding="utf-8")
        self.assertIn('app.setApplicationVersion("3.1")', main)

    def test_release_script_builds_2_1_checksum_and_checklist(self):
        script = PACKAGE_SCRIPT.read_text(encoding="utf-8")
        self.assertEqual(package_release.VERSION, "3.1")
        self.assertEqual(package_release.ZIP_PATH.name, "定时关机助手-3.1.zip")
        self.assertEqual(package_release.SHA256SUMS_PATH.name, "SHA256SUMS.txt")
        self.assertEqual(package_release.RELEASE_CHECKLIST_PATH.name, "release-checklist-v3.1.md")
        self.assertIn('create_sha256sums', script)
        self.assertIn('create_release_checklist', script)

    def test_checksum_file_contains_archive_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "定时关机助手-3.1.zip"
            archive_path.write_bytes(b"demo")

            sums = package_release.create_sha256sums(archive_path, Path(tmp) / "SHA256SUMS.txt")
            content = sums.read_text(encoding="utf-8")

            self.assertIn("定时关机助手-3.1.zip", content)
            self.assertRegex(content, r"^[0-9a-f]{64}  定时关机助手-3.1.zip")

    def test_checksum_file_contains_archive_and_installer_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "定时关机助手-3.1.zip"
            setup_path = Path(tmp) / "定时关机助手-3.1-Setup.exe"
            archive_path.write_bytes(b"zip")
            setup_path.write_bytes(b"setup")

            sums = package_release.create_sha256sums([archive_path, setup_path], Path(tmp) / "SHA256SUMS.txt")
            content = sums.read_text(encoding="utf-8")

            self.assertIn("定时关机助手-3.1.zip", content)
            self.assertIn("定时关机助手-3.1-Setup.exe", content)
            self.assertEqual(len([line for line in content.splitlines() if line]), 2)

    def test_release_checklist_mentions_dry_run_and_no_real_power_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            checklist = package_release.create_release_checklist(Path(tmp) / "release-checklist-v3.1.md")
            content = checklist.read_text(encoding="utf-8")

            self.assertIn("Dry-run", content)
            self.assertIn("Do not execute real shutdown", content)
            self.assertIn("SHA256SUMS.txt", content)
    def test_main_declares_final_2_3_version(self):
        main = MAIN_PY.read_text(encoding="utf-8")
        self.assertIn('app.setApplicationVersion("3.1")', main)

    def test_release_script_builds_2_3_artifacts(self):
        self.assertEqual(package_release.VERSION, "3.1")
        self.assertEqual(package_release.SPEC_FILE.name, "AutoShutdownQt-3.1.spec")
        self.assertEqual(package_release.ZIP_PATH.name, "定时关机助手-3.1.zip")
        self.assertEqual(package_release.RELEASE_CHECKLIST_PATH.name, "release-checklist-v3.1.md")

    def test_release_checklist_mentions_command_center_and_recent_activity(self):
        with tempfile.TemporaryDirectory() as tmp:
            checklist = package_release.create_release_checklist(Path(tmp) / "release-checklist-v3.1.md")
            content = checklist.read_text(encoding="utf-8")

            self.assertIn("Command Center", content)
            self.assertIn("Queue health", content)
            self.assertIn("Recent activity", content)

    def test_release_notes_document_2_3_command_center_patch(self):
        notes = (ROOT / "RELEASE_NOTES_v3.1.md").read_text(encoding="utf-8")
        self.assertIn("3.1", notes)
        self.assertIn("command center", notes.lower())
        self.assertIn("queue", notes.lower())
        self.assertIn("tray", notes.lower())
        self.assertIn("SHA256SUMS.txt", notes)

    def test_release_checklist_mentions_2_5_background_features(self):
        with tempfile.TemporaryDirectory() as tmp:
            checklist = package_release.create_release_checklist(Path(tmp) / "release-checklist-v3.1.md")
            content = checklist.read_text(encoding="utf-8")

            self.assertIn("Windows native notification", content)
            self.assertIn("task history", content)
            self.assertIn("startup", content)
            self.assertIn("close button", content)
            self.assertIn("right-bottom tray icon", content)
            self.assertIn("double-clicking the tray icon", content)
            self.assertIn("tray menu Quit", content)
            self.assertIn("idle auto-shutdown", content)
            self.assertIn("idle queue task", content)

    def test_readme_mentions_2_3_download_and_checksum(self):
        readme = README.read_text(encoding="utf-8")
        self.assertIn("定时关机助手 3.1", readme)
        self.assertIn("定时关机助手-3.1.zip", readme)
        self.assertIn("SHA256SUMS.txt", readme)

    def test_readme_mentions_idle_auto_shutdown(self):
        readme = README.read_text(encoding="utf-8")
        self.assertIn("空闲自动关机", readme)
        self.assertIn("空闲分钟", readme)

    def test_readme_github_release_instructions_use_v3_1_artifacts(self):
        readme = README.read_text(encoding="utf-8")
        self.assertIn("`v3.1` tag", readme)
        self.assertIn("AutoShutdownQt-3.1-Setup.exe", readme)
        self.assertIn("AutoShutdownQt-3.1.zip", readme)
        self.assertIn("显示名称：定时关机助手-3.1-Setup.exe", readme)
        self.assertIn("显示名称：定时关机助手-3.1.zip", readme)
        self.assertNotIn("`v3.0` tag", readme)
        self.assertNotIn("dist/AutoShutdownQt-3.0-Setup.exe", readme)
        self.assertNotIn("dist/AutoShutdownQt-3.0.zip", readme)

    def test_inno_setup_script_builds_installable_3_0_setup(self):
        script = INNO_SCRIPT.read_text(encoding="utf-8")

        self.assertRegex(script, r"AppId=\{\{[0-9A-Fa-f-]{36}\}")
        self.assertIn('#define MyAppName "定时关机助手"', script)
        self.assertIn('#define MyAppVersion "3.1"', script)
        self.assertIn('OutputBaseFilename=定时关机助手-3.1-Setup', script)
        self.assertIn("SetupIconFile=app_icon.ico", script)
        self.assertIn("UninstallDisplayIcon", script)
        self.assertIn('Source: "..\\dist\\定时关机助手-3.1\\*"; DestDir: "{app}"', script)
        self.assertIn('Name: "{autodesktop}\\定时关机助手"', script)
        self.assertIn('Name: "{group}\\定时关机助手"', script)
        self.assertIn('Name: "{group}\\卸载定时关机助手"', script)
        self.assertIn('Description: "安装后启动定时关机助手"', script)

    def test_release_script_builds_zip_and_inno_installer_artifacts(self):
        script = PACKAGE_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(package_release.VERSION, "3.1")
        self.assertEqual(package_release.ZIP_PATH.name, "定时关机助手-3.1.zip")
        self.assertIn("LOCALAPPDATA", script)
        self.assertIn("Inno Setup 6", script)
        self.assertEqual(package_release.INNO_SCRIPT.name, "AutoShutdownQt-3.1.iss")
        self.assertEqual(package_release.SETUP_PATH.name, "定时关机助手-3.1-Setup.exe")
        self.assertIn('build_inno_installer', script)

    def test_v3_1_release_metadata_uses_chinese_artifact_names(self):
        main = MAIN_PY.read_text(encoding="utf-8")
        readme = README.read_text(encoding="utf-8")

        self.assertIn('app.setApplicationVersion("3.1")', main)
        self.assertEqual(package_release.VERSION, "3.1")
        self.assertEqual(package_release.APP_BUNDLE_NAME, "定时关机助手-3.1")
        self.assertEqual(package_release.APP_BUNDLE_DIR.name, "定时关机助手-3.1")
        self.assertEqual(package_release.ZIP_PATH.name, "定时关机助手-3.1.zip")
        self.assertEqual(package_release.SETUP_PATH.name, "定时关机助手-3.1-Setup.exe")
        self.assertEqual(package_release.REQUIRED_EXE, "定时关机助手-3.1/定时关机助手.exe")
        self.assertEqual(package_release.SPEC_FILE.name, "AutoShutdownQt-3.1.spec")
        self.assertEqual(package_release.INNO_SCRIPT.name, "AutoShutdownQt-3.1.iss")
        self.assertIn('定时关机助手 3.1', readme)
        self.assertIn('定时关机助手-3.1.zip', readme)
        self.assertIn('定时关机助手-3.1-Setup.exe', readme)


if __name__ == "__main__":
    unittest.main()
