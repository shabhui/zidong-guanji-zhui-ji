import json
import shutil
import struct
import sys
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
MAIN_PY = APP_DIR / "main.py"
SPEC = APP_DIR / "AutoShutdownQt-4.0.spec"
INNO_SCRIPT = APP_DIR / "AutoShutdownQt-4.0.iss"
PACKAGE_SCRIPT = APP_DIR / "package_release.py"
README = ROOT / "README.md"
sys.path.insert(0, str(APP_DIR))

import package_release


class ReleasePackagingTest(unittest.TestCase):
    def _workspace_scratch(self, name):
        target = ROOT / "test-tmp" / name
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        target.mkdir(parents=True, exist_ok=True)
        self.addCleanup(lambda: shutil.rmtree(target, ignore_errors=True))
        return target

    def _valid_manifest(self, archive_name="定时关机助手-4.0.zip", bundle="定时关机助手-4.0"):
        return {
            "app": "定时关机助手",
            "version": "4.0",
            "bundle": bundle,
            "executable": "定时关机助手.exe",
            "archive": archive_name,
            "checks": {
                "executablePresent": True,
                "mainQmlPresent": True,
                "taskSchedulerIncluded": True,
                "bundledMusicPresent": True,
                "appCloseServiceHiddenImport": True,
                "diagnosticsCenterWired": True,
                "supportWorkflowWired": True,
                "failedQueueRecoveryWired": True,
            },
            "safetyNotes": [
                "默认开启安全验证模式。",
                "真实执行模式会调用 Windows 电源动作。",
            ],
        }

    def _write_valid_archive(self, archive_path, manifest=None):
        manifest = self._valid_manifest(archive_path.name) if manifest is None else manifest
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("定时关机助手-4.0/定时关机助手.exe", "exe")
            archive.writestr("定时关机助手-4.0/_internal/qml/Main.qml", "qml")
            archive.writestr("定时关机助手-4.0/release-manifest.json", json.dumps(manifest))
            archive.writestr("定时关机助手-4.0/demo.mp3", b"mp3")
    def test_main_declares_final_2_5_version(self):
        main = MAIN_PY.read_text(encoding="utf-8")
        self.assertIn('app.setApplicationVersion("4.0")', main)
        self.assertNotIn("3.0-preview", main)

    def test_pyinstaller_spec_includes_qml_and_runtime_modules(self):
        spec = SPEC.read_text(encoding="utf-8")
        self.assertIn("定时关机助手-4.0", spec)
        self.assertIn("main.py", spec)
        self.assertIn("qml", spec)
        self.assertIn("controller", spec)
        self.assertIn("settings_service", spec)
        self.assertIn("network_service", spec)
        self.assertIn("power_service", spec)
        self.assertIn("script_service", spec)
        self.assertIn("app_close_service", spec)
        self.assertIn("music_service", spec)
        self.assertIn("PySide6.QtQml", spec)
        self.assertIn("PySide6.QtQuick", spec)
        self.assertIn("PySide6.QtQuickControls2", spec)
        self.assertIn("app_icon.png", spec)
        self.assertIn("app_icon.ico", spec)
        self.assertIn("icon=", spec)

    def test_app_icon_png_is_release_ready_not_photographic_placeholder(self):
        icon_path = APP_DIR / "app_icon.png"
        data = icon_path.read_bytes()
        width, height = struct.unpack(">II", data[16:24])

        self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual((width, height), (512, 512))
        self.assertLess(icon_path.stat().st_size, 512 * 1024)

    def test_pyinstaller_hiddenimports_use_module_names_not_py_files(self):
        spec = SPEC.read_text(encoding="utf-8")
        self.assertNotIn('"controller.py",', spec)
        self.assertNotIn('"settings_service.py",', spec)
        self.assertNotIn('"network_service.py",', spec)
        self.assertNotIn('"power_service.py",', spec)
        self.assertNotIn('"script_service.py",', spec)

    def test_gitignore_allows_release_spec_to_be_committed(self):
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("!AutoShutdownQt/AutoShutdownQt-4.0.spec", gitignore)

    def test_gitignore_excludes_local_runtime_and_visual_test_outputs(self):
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

        for pattern in (
            ".codex_pydeps/",
            ".codex-marketplace-test/",
            ".tmp/",
            "test-tmp/",
            "AutoShutdownQt/screenshots/",
            "AutoShutdownQt/ui_screenshots/",
            "AutoShutdownQt/ui_page*.png",
            "AutoShutdownQt/ui_overview.png",
        ):
            self.assertIn(pattern, gitignore)

    def test_release_script_builds_versioned_zip_from_spec(self):
        script = PACKAGE_SCRIPT.read_text(encoding="utf-8")
        self.assertEqual(package_release.VERSION, "4.0")
        self.assertEqual(package_release.SPEC_FILE.name, "AutoShutdownQt-4.0.spec")
        self.assertEqual(package_release.APP_BUNDLE_DIR.name, "定时关机助手-4.0")
        self.assertEqual(package_release.ZIP_PATH.name, "定时关机助手-4.0.zip")
        self.assertIn("PyInstaller", script)
        self.assertIn("zipfile", script)
        self.assertIn("validate_zip_contents", script)

    def test_release_script_copies_root_mp3_into_bundle(self):
        root = self._workspace_scratch("release-music-copy")
        bundle = root / "dist" / package_release.APP_BUNDLE_DIR.name
        bundle.mkdir(parents=True)
        (root / "theme.mp3").write_bytes(b"mp3")

        copied = package_release.copy_bundled_music(root, bundle)

        self.assertEqual(copied, [bundle / "theme.mp3"])
        self.assertEqual((bundle / "theme.mp3").read_bytes(), b"mp3")

    def test_release_script_prunes_unused_qt_payload_after_pyinstaller(self):
        root = self._workspace_scratch("release-prune-qt-payload")
        bundle = root / package_release.APP_BUNDLE_DIR.name
        keep_file = bundle / "_internal" / "PySide6" / "Qt6Quick.dll"
        webengine_file = bundle / "_internal" / "PySide6" / "Qt6WebEngineCore.dll"
        virtual_keyboard_file = bundle / "_internal" / "PySide6" / "qml" / "QtQuick" / "VirtualKeyboard" / "qtvkbplugin.dll"
        virtual_keyboard_runtime_file = bundle / "_internal" / "PySide6" / "Qt6VirtualKeyboard.dll"
        quick3d_file = bundle / "_internal" / "PySide6" / "qml" / "QtQuick3D" / "qtquick3dplugin.dll"
        quick3d_runtime_file = bundle / "_internal" / "PySide6" / "Qt6Quick3DRuntimeRender.dll"
        webview_runtime_file = bundle / "_internal" / "PySide6" / "Qt6WebView.dll"
        webchannel_runtime_file = bundle / "_internal" / "PySide6" / "Qt6WebChannel.dll"
        websockets_runtime_file = bundle / "_internal" / "PySide6" / "Qt6WebSockets.dll"
        text_to_speech_runtime_file = bundle / "_internal" / "PySide6" / "Qt6TextToSpeech.dll"
        webchannel_qml_file = bundle / "_internal" / "PySide6" / "qml" / "QtWebChannel" / "declarative_webchannel.dll"
        music_file = bundle / "theme.mp3"
        for path in (
            keep_file,
            webengine_file,
            virtual_keyboard_file,
            virtual_keyboard_runtime_file,
            quick3d_file,
            quick3d_runtime_file,
            webview_runtime_file,
            webchannel_runtime_file,
            websockets_runtime_file,
            text_to_speech_runtime_file,
            webchannel_qml_file,
            music_file,
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"payload")

        removed = package_release.prune_unused_qt_payload(bundle)

        self.assertFalse(webengine_file.exists())
        self.assertFalse(virtual_keyboard_file.exists())
        self.assertFalse(virtual_keyboard_runtime_file.exists())
        self.assertFalse(quick3d_file.exists())
        self.assertFalse(quick3d_runtime_file.exists())
        self.assertFalse(webview_runtime_file.exists())
        self.assertFalse(webchannel_runtime_file.exists())
        self.assertFalse(websockets_runtime_file.exists())
        self.assertFalse(text_to_speech_runtime_file.exists())
        self.assertFalse(webchannel_qml_file.exists())
        self.assertTrue(keep_file.exists())
        self.assertTrue(music_file.exists())
        self.assertEqual(removed, 10)

    def test_release_archive_validation_rejects_pruned_qt_payload_regressions(self):
        root = self._workspace_scratch("release-reject-pruned-qt-payload")
        archive_path = root / package_release.ZIP_PATH.name
        self._write_valid_archive(archive_path)
        with zipfile.ZipFile(archive_path, "a") as archive:
            archive.writestr("定时关机助手-4.0/_internal/PySide6/Qt6WebEngineCore.dll", b"web")

        with self.assertRaisesRegex(RuntimeError, "unused Qt payload"):
            package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_passes_with_required_qt_payload(self):
        root = self._workspace_scratch("release-required-qt-payload")
        archive_path = root / package_release.ZIP_PATH.name
        self._write_valid_archive(archive_path)
        with zipfile.ZipFile(archive_path, "a") as archive:
            archive.writestr("定时关机助手-4.0/_internal/PySide6/Qt6Quick.dll", b"quick")
            archive.writestr("定时关机助手-4.0/_internal/PySide6/qml/QtQuick/Controls/qmldir", b"controls")

        self.assertTrue(package_release.validate_zip_contents(archive_path))

    def test_release_archive_validation_fails_when_music_is_missing(self):
        root = self._workspace_scratch("release-missing-music")
        archive_path = root / package_release.ZIP_PATH.name
        manifest = self._valid_manifest(archive_path.name)
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("定时关机助手-4.0/定时关机助手.exe", "exe")
            archive.writestr("定时关机助手-4.0/_internal/qml/Main.qml", "qml")
            archive.writestr("定时关机助手-4.0/release-manifest.json", json.dumps(manifest))

        with self.assertRaisesRegex(RuntimeError, "music"):
            package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_passes_when_exe_qml_music_and_matching_manifest_are_present(self):
        root = self._workspace_scratch("release-valid-archive")
        archive_path = root / package_release.ZIP_PATH.name
        self._write_valid_archive(archive_path)

        self.assertTrue(package_release.validate_zip_contents(archive_path))

    def test_release_archive_validation_fails_when_manifest_is_empty(self):
        root = self._workspace_scratch("release-empty-manifest")
        archive_path = root / package_release.ZIP_PATH.name
        self._write_valid_archive(archive_path, manifest={})

        with self.assertRaisesRegex(RuntimeError, "manifest.*version"):
            package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_fails_when_manifest_is_stale(self):
        root = self._workspace_scratch("release-stale-manifest")
        archive_path = root / package_release.ZIP_PATH.name
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
                root = self._workspace_scratch(f"release-stale-identity-{field}")
                archive_path = root / package_release.ZIP_PATH.name
                manifest = self._valid_manifest(archive_path.name)
                manifest[field] = stale_value
                self._write_valid_archive(archive_path, manifest=manifest)

                with self.assertRaisesRegex(RuntimeError, expected_error):
                    package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_fails_when_manifest_checks_disagree_with_contents(self):
        stale_checks = ("executablePresent", "mainQmlPresent")
        for check_name in stale_checks:
            with self.subTest(check_name=check_name):
                root = self._workspace_scratch(f"release-stale-check-{check_name}")
                archive_path = root / package_release.ZIP_PATH.name
                manifest = self._valid_manifest(archive_path.name)
                manifest["checks"][check_name] = False
                self._write_valid_archive(archive_path, manifest=manifest)

                with self.assertRaisesRegex(RuntimeError, f"manifest.*{check_name}"):
                    package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_fails_when_exe_is_missing(self):
        root = self._workspace_scratch("release-missing-exe")
        archive_path = root / package_release.ZIP_PATH.name
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("定时关机助手-4.0/_internal/qml/Main.qml", "qml")

        with self.assertRaisesRegex(RuntimeError, "定时关机助手.exe"):
            package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_fails_when_qml_is_missing(self):
        root = self._workspace_scratch("release-missing-qml")
        archive_path = root / package_release.ZIP_PATH.name
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("定时关机助手-4.0/定时关机助手.exe", "exe")
            archive.writestr("定时关机助手-4.0/release-manifest.json", json.dumps(self._valid_manifest(archive_path.name)))

        with self.assertRaisesRegex(RuntimeError, "QML"):
            package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_fails_when_main_qml_is_missing(self):
        root = self._workspace_scratch("release-missing-main-qml")
        archive_path = root / package_release.ZIP_PATH.name
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("定时关机助手-4.0/定时关机助手.exe", "exe")
            archive.writestr("定时关机助手-4.0/_internal/qml/Theme.qml", "qml")
            archive.writestr("定时关机助手-4.0/release-manifest.json", json.dumps(self._valid_manifest(archive_path.name)))

        with self.assertRaisesRegex(RuntimeError, "Main.qml"):
            package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_fails_when_manifest_is_missing(self):
        root = self._workspace_scratch("release-missing-manifest")
        archive_path = root / package_release.ZIP_PATH.name
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("定时关机助手-4.0/定时关机助手.exe", "exe")
            archive.writestr("定时关机助手-4.0/_internal/qml/Main.qml", "qml")

        with self.assertRaisesRegex(RuntimeError, "release-manifest.json"):
            package_release.validate_zip_contents(archive_path)

    def test_release_manifest_records_version_and_safety_notes(self):
        root = self._workspace_scratch("release-manifest-records")
        bundle = root / "定时关机助手-4.0"
        (bundle / "_internal" / "qml").mkdir(parents=True)
        (bundle / "定时关机助手.exe").write_text("exe", encoding="utf-8")
        (bundle / "_internal" / "qml" / "Main.qml").write_text("qml", encoding="utf-8")

        manifest_path = package_release.create_release_manifest(bundle)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["version"], "4.0")
        self.assertEqual(manifest["executable"], "定时关机助手.exe")
        self.assertTrue(manifest["checks"]["mainQmlPresent"])
        self.assertTrue(manifest["checks"]["appCloseServiceHiddenImport"])
        self.assertTrue(manifest["checks"]["diagnosticsCenterWired"])
        self.assertTrue(manifest["checks"]["supportWorkflowWired"])
        self.assertTrue(manifest["checks"]["failedQueueRecoveryWired"])
        safety_notes = " ".join(manifest["safetyNotes"])
        self.assertIn("安全验证", safety_notes)
        self.assertIn("真实执行模式", safety_notes)
        self.assertNotIn("Dry-run", safety_notes)

    def test_release_notes_document_portable_safety_mode_and_unsigned_status(self):
        notes = (ROOT / "RELEASE_NOTES_v4.0.md").read_text(encoding="utf-8")
        self.assertIn("安全验证", notes)
        self.assertNotIn("Dry-run", notes)
        self.assertIn("便携版", notes)
        self.assertIn("未做代码签名", notes)
        self.assertIn("dist/定时关机助手-4.0.zip", notes)

    def test_readme_current_release_status_mentions_main_not_old_feature_branch(self):
        readme = README.read_text(encoding="utf-8")
        self.assertIn("main", readme)
        self.assertNotIn("v2-e5e8-reference-ui", readme)

    def test_readme_safety_copy_uses_product_chinese(self):
        readme = README.read_text(encoding="utf-8")

        self.assertIn("安全验证模式", readme)
        self.assertIn("真实执行模式", readme)
        self.assertNotIn("Dry-run", readme)
        self.assertNotIn("dry-run", readme)

    def test_main_declares_final_2_1_version(self):
        main = MAIN_PY.read_text(encoding="utf-8")
        self.assertIn('app.setApplicationVersion("4.0")', main)

    def test_release_script_builds_2_1_checksum_and_checklist(self):
        script = PACKAGE_SCRIPT.read_text(encoding="utf-8")
        self.assertEqual(package_release.VERSION, "4.0")
        self.assertEqual(package_release.ZIP_PATH.name, "定时关机助手-4.0.zip")
        self.assertEqual(package_release.SHA256SUMS_PATH.name, "SHA256SUMS.txt")
        self.assertEqual(package_release.RELEASE_CHECKLIST_PATH.name, "release-checklist-v4.0.md")
        self.assertIn('create_sha256sums', script)
        self.assertIn('create_release_checklist', script)

    def test_checksum_file_contains_archive_hash(self):
        root = self._workspace_scratch("release-checksum-archive")
        archive_path = root / package_release.ZIP_PATH.name
        archive_path.write_bytes(b"demo")

        sums = package_release.create_sha256sums(archive_path, root / "SHA256SUMS.txt")
        content = sums.read_text(encoding="utf-8")

        self.assertIn("定时关机助手-4.0.zip", content)
        self.assertRegex(content, r"^[0-9a-f]{64}  定时关机助手-4.0.zip")

    def test_checksum_file_streams_artifacts_without_reading_all_bytes(self):
        root = self._workspace_scratch("release-checksum-streaming")
        archive_path = root / package_release.ZIP_PATH.name
        archive_path.write_bytes(b"demo")

        with patch.object(Path, "read_bytes", side_effect=AssertionError("use streaming checksum")):
            sums = package_release.create_sha256sums(archive_path, root / "SHA256SUMS.txt")

        self.assertRegex(sums.read_text(encoding="utf-8"), r"^[0-9a-f]{64}  ")

    def test_checksum_file_contains_archive_and_installer_hashes(self):
        root = self._workspace_scratch("release-checksum-archive-installer")
        archive_path = root / package_release.ZIP_PATH.name
        setup_path = root / package_release.SETUP_PATH.name
        archive_path.write_bytes(b"zip")
        setup_path.write_bytes(b"setup")

        sums = package_release.create_sha256sums([archive_path, setup_path], root / "SHA256SUMS.txt")
        content = sums.read_text(encoding="utf-8")

        self.assertIn("定时关机助手-4.0.zip", content)
        self.assertIn("定时关机助手-4.0-Setup.exe", content)
        self.assertEqual(len([line for line in content.splitlines() if line]), 2)

    def test_release_checklist_mentions_safety_mode_and_no_real_power_actions(self):
        root = self._workspace_scratch("release-checklist-safety")
        checklist = package_release.create_release_checklist(root / "release-checklist-v4.0.md")
        content = checklist.read_text(encoding="utf-8")

        self.assertIn("安全验证", content)
        self.assertIn("不要执行真实的关机", content)
        self.assertIn("SHA256SUMS.txt", content)
        self.assertNotIn("Dry-run", content)
        self.assertNotIn("LIVE MODE", content)
    def test_main_declares_final_2_3_version(self):
        main = MAIN_PY.read_text(encoding="utf-8")
        self.assertIn('app.setApplicationVersion("4.0")', main)

    def test_release_script_builds_2_3_artifacts(self):
        self.assertEqual(package_release.VERSION, "4.0")
        self.assertEqual(package_release.SPEC_FILE.name, "AutoShutdownQt-4.0.spec")
        self.assertEqual(package_release.ZIP_PATH.name, "定时关机助手-4.0.zip")
        self.assertEqual(package_release.RELEASE_CHECKLIST_PATH.name, "release-checklist-v4.0.md")

    def test_release_checklist_mentions_command_center_and_recent_activity(self):
        root = self._workspace_scratch("release-checklist-command-center")
        checklist = package_release.create_release_checklist(root / "release-checklist-v4.0.md")
        content = checklist.read_text(encoding="utf-8")

        self.assertIn("指挥中心", content)
        self.assertIn("队列健康", content)
        self.assertIn("最近活动", content)

    def test_release_notes_document_2_3_command_center_patch(self):
        notes = (ROOT / "RELEASE_NOTES_v4.0.md").read_text(encoding="utf-8")
        self.assertIn("4.0", notes)
        self.assertIn("指挥中心", notes)
        self.assertIn("队列", notes)
        self.assertIn("托盘", notes)
        self.assertIn("SHA256SUMS.txt", notes)

    def test_release_checklist_mentions_2_5_background_features(self):
        root = self._workspace_scratch("release-checklist-background")
        checklist = package_release.create_release_checklist(root / "release-checklist-v4.0.md")
        content = checklist.read_text(encoding="utf-8")

        self.assertIn("Windows 原生通知", content)
        self.assertIn("任务历史", content)
        self.assertIn("开机启动", content)
        self.assertIn("关闭按钮", content)
        self.assertIn("右下角托盘图标", content)
        self.assertIn("双击托盘图标", content)
        self.assertIn("托盘菜单“退出程序”", content)
        self.assertIn("空闲自动关机", content)
        self.assertIn("空闲队列任务", content)
        self.assertIn("关机前优雅关闭应用", content)
        self.assertIn("安全验证下的关闭应用预览", content)
        self.assertIn("真实执行关闭应用验证", content)
        self.assertIn("关闭应用预检", content)
        self.assertIn("AUTOSHUTDOWNQT_REAL_WINDOW_SMOKE=1", content)
        self.assertIn("导出的诊断信息包含关闭应用状态", content)
        self.assertIn("安全摘要", content)
        self.assertIn("触发器状态", content)
        self.assertIn("日志分类", content)
        self.assertIn("复制诊断写入剪贴板", content)
        self.assertIn("日志筛选", content)
        self.assertIn("一键健康检查", content)
        self.assertIn("失败队列任务重试", content)
        self.assertIn("复制队列任务诊断", content)

    def test_readme_mentions_2_3_download_and_checksum(self):
        readme = README.read_text(encoding="utf-8")
        self.assertIn("定时关机助手 4.0", readme)
        self.assertIn("定时关机助手-4.0.zip", readme)
        self.assertIn("SHA256SUMS.txt", readme)

    def test_readme_mentions_idle_auto_shutdown(self):
        readme = README.read_text(encoding="utf-8")
        self.assertIn("空闲自动关机", readme)
        self.assertIn("空闲分钟", readme)

    def test_readme_keeps_python_3_12_requirement(self):
        readme = README.read_text(encoding="utf-8")
        self.assertIn("Python 3.12+", readme)
        self.assertNotIn("Python 3.22+", readme)

    def test_readme_github_release_instructions_use_v3_1_artifacts(self):
        readme = README.read_text(encoding="utf-8")
        self.assertIn("`v4.0` tag", readme)
        self.assertIn("dist/定时关机助手-4.0-Setup.exe", readme)
        self.assertIn("dist/定时关机助手-4.0.zip", readme)
        self.assertNotIn("AutoShutdownQt-4.0-Setup.exe", readme)
        self.assertNotIn("AutoShutdownQt-4.0.zip", readme)
        self.assertNotIn("`v3.0` tag", readme)
        self.assertNotIn("dist/AutoShutdownQt-3.0-Setup.exe", readme)
        self.assertNotIn("dist/AutoShutdownQt-3.0.zip", readme)

    def test_readme_current_release_section_is_chinese(self):
        readme = README.read_text(encoding="utf-8")
        current = readme[readme.index("## Current release"):readme.index("## 功能特性")]

        self.assertIn("当前版本", current)
        self.assertIn("下载安装器", current)
        self.assertIn("便携版 zip", current)
        self.assertIn("校验文件", current)
        self.assertNotIn("Download installer", current)
        self.assertNotIn("Portable zip", current)
        self.assertNotIn("Verify checksum", current)
        self.assertNotIn("Dry-run is enabled by default", current)

    def test_inno_setup_script_builds_installable_3_0_setup(self):
        script = INNO_SCRIPT.read_text(encoding="utf-8")

        self.assertRegex(script, r"AppId=\{\{[0-9A-Fa-f-]{36}\}")
        self.assertIn('#define MyAppName "定时关机助手"', script)
        self.assertIn('#define MyAppVersion "4.0"', script)
        self.assertIn('OutputBaseFilename=定时关机助手-4.0-Setup', script)
        self.assertIn("SetupIconFile=app_icon.ico", script)
        self.assertIn("UninstallDisplayIcon", script)
        self.assertIn("ArchitecturesInstallIn64BitMode=x64compatible", script)
        self.assertNotIn("ArchitecturesInstallIn64BitMode=x64\n", script)
        self.assertIn('Source: "..\\dist\\定时关机助手-4.0\\*"; DestDir: "{app}"', script)
        self.assertIn('Name: "{autodesktop}\\定时关机助手"', script)
        self.assertIn('Name: "{group}\\定时关机助手"', script)
        self.assertIn('Name: "{group}\\卸载定时关机助手"', script)
        self.assertIn('Description: "安装后启动定时关机助手"', script)

    def test_release_script_builds_zip_and_inno_installer_artifacts(self):
        script = PACKAGE_SCRIPT.read_text(encoding="utf-8")

        self.assertEqual(package_release.VERSION, "4.0")
        self.assertEqual(package_release.ZIP_PATH.name, "定时关机助手-4.0.zip")
        self.assertIn("LOCALAPPDATA", script)
        self.assertIn("Inno Setup 6", script)
        self.assertEqual(package_release.INNO_SCRIPT.name, "AutoShutdownQt-4.0.iss")
        self.assertEqual(package_release.SETUP_PATH.name, "定时关机助手-4.0-Setup.exe")
        self.assertIn('build_inno_installer', script)

    def test_v3_1_release_metadata_uses_chinese_artifact_names(self):
        main = MAIN_PY.read_text(encoding="utf-8")
        readme = README.read_text(encoding="utf-8")

        self.assertIn('app.setApplicationVersion("4.0")', main)
        self.assertEqual(package_release.VERSION, "4.0")
        self.assertEqual(package_release.APP_BUNDLE_NAME, "定时关机助手-4.0")
        self.assertEqual(package_release.APP_BUNDLE_DIR.name, "定时关机助手-4.0")
        self.assertEqual(package_release.ZIP_PATH.name, "定时关机助手-4.0.zip")
        self.assertEqual(package_release.SETUP_PATH.name, "定时关机助手-4.0-Setup.exe")
        self.assertEqual(package_release.REQUIRED_EXE, "定时关机助手-4.0/定时关机助手.exe")
        self.assertEqual(package_release.SPEC_FILE.name, "AutoShutdownQt-4.0.spec")
        self.assertEqual(package_release.INNO_SCRIPT.name, "AutoShutdownQt-4.0.iss")
        self.assertIn('定时关机助手 4.0', readme)
        self.assertIn('定时关机助手-4.0.zip', readme)
        self.assertIn('定时关机助手-4.0-Setup.exe', readme)


if __name__ == "__main__":
    unittest.main()
