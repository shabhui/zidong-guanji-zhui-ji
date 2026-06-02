import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
MAIN_PY = APP_DIR / "main.py"
SPEC = APP_DIR / "AutoShutdownQt-2.0.spec"
PACKAGE_SCRIPT = APP_DIR / "package_release.py"


class ReleasePackagingTest(unittest.TestCase):
    def test_main_declares_final_2_0_version(self):
        main = MAIN_PY.read_text(encoding="utf-8")
        self.assertIn('app.setApplicationVersion("2.0")', main)
        self.assertNotIn("2.0-preview", main)

    def test_pyinstaller_spec_includes_qml_and_runtime_modules(self):
        spec = SPEC.read_text(encoding="utf-8")
        self.assertIn("AutoShutdownQt-2.0", spec)
        self.assertIn("main.py", spec)
        self.assertIn("qml", spec)
        self.assertIn("controller", spec)
        self.assertIn("settings_service", spec)
        self.assertIn("network_service", spec)
        self.assertIn("power_service", spec)
        self.assertIn("script_service", spec)
        self.assertIn("PySide6.QtQml", spec)
        self.assertIn("PySide6.QtQuick", spec)
        self.assertIn("PySide6.QtQuickControls2", spec)

    def test_pyinstaller_hiddenimports_use_module_names_not_py_files(self):
        spec = SPEC.read_text(encoding="utf-8")
        self.assertNotIn('"controller.py",', spec)
        self.assertNotIn('"settings_service.py",', spec)
        self.assertNotIn('"network_service.py",', spec)
        self.assertNotIn('"power_service.py",', spec)
        self.assertNotIn('"script_service.py",', spec)

    def test_gitignore_allows_release_spec_to_be_committed(self):
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("!AutoShutdownQt/AutoShutdownQt-2.0.spec", gitignore)

    def test_release_script_builds_versioned_zip_from_spec(self):
        script = PACKAGE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn('VERSION = "2.0"', script)
        self.assertIn('SPEC_FILE = APP_DIR / "AutoShutdownQt-2.0.spec"', script)
        self.assertIn('DIST_DIR / "AutoShutdownQt-2.0"', script)
        self.assertIn('AutoShutdownQt-2.0.zip', script)
        self.assertIn("PyInstaller", script)
        self.assertIn("zipfile", script)


if __name__ == "__main__":
    unittest.main()
