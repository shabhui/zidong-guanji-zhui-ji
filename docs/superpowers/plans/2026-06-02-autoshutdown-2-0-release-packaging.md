# AutoShutdownQt 2.0 Release Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a Windows AutoShutdownQt 2.0 distributable directory and zip artifact with release metadata committed to the repo.

**Architecture:** Keep the app entrypoint as `AutoShutdownQt/main.py` and update its runtime version string to `2.0`. Add a focused PyInstaller spec and release helper script that package Python modules plus the QML tree into `dist/AutoShutdownQt-2.0/`. Add release tests that verify version metadata and packaging configuration without building the binary.

**Tech Stack:** Python 3.12, PySide6/QML, PyInstaller, Python `unittest`, Windows zip artifact.

---

## Files

- Modify: `AutoShutdownQt/main.py` — change `app.setApplicationVersion("2.0-preview")` to `app.setApplicationVersion("2.0")`.
- Create: `AutoShutdownQt/AutoShutdownQt-2.0.spec` — PyInstaller spec for one-folder app packaging with QML assets.
- Create: `AutoShutdownQt/package_release.py` — release helper that runs PyInstaller and creates `dist/AutoShutdownQt-2.0.zip`.
- Create: `AutoShutdownQt/tests/test_release_packaging.py` — release metadata/spec tests.

## Task 1: Version Metadata Test

**Files:**
- Create: `AutoShutdownQt/tests/test_release_packaging.py`
- Modify: `AutoShutdownQt/main.py`

- [ ] **Step 1: Write failing version test**

```python
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
MAIN_PY = APP_DIR / "main.py"


class ReleasePackagingTest(unittest.TestCase):
    def test_main_declares_final_2_0_version(self):
        main = MAIN_PY.read_text(encoding="utf-8")
        self.assertIn('app.setApplicationVersion("2.0")', main)
        self.assertNotIn("2.0-preview", main)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify red**

Run: `python -m unittest AutoShutdownQt/tests/test_release_packaging.py -v`
Expected: FAIL because `main.py` still contains `2.0-preview`.

- [ ] **Step 3: Update version**

Change `AutoShutdownQt/main.py` line 10 from:

```python
app.setApplicationVersion("2.0-preview")
```

to:

```python
app.setApplicationVersion("2.0")
```

- [ ] **Step 4: Run test to verify green**

Run: `python -m unittest AutoShutdownQt/tests/test_release_packaging.py -v`
Expected: PASS.

## Task 2: PyInstaller Spec Test and Config

**Files:**
- Modify: `AutoShutdownQt/tests/test_release_packaging.py`
- Create: `AutoShutdownQt/AutoShutdownQt-2.0.spec`

- [ ] **Step 1: Extend failing spec test**

Add to `ReleasePackagingTest`:

```python
SPEC = APP_DIR / "AutoShutdownQt-2.0.spec"

    def test_pyinstaller_spec_includes_qml_and_runtime_modules(self):
        spec = SPEC.read_text(encoding="utf-8")
        self.assertIn("AutoShutdownQt-2.0", spec)
        self.assertIn("main.py", spec)
        self.assertIn("qml", spec)
        self.assertIn("controller.py", spec)
        self.assertIn("settings_service.py", spec)
        self.assertIn("network_service.py", spec)
        self.assertIn("power_service.py", spec)
        self.assertIn("script_service.py", spec)
        self.assertIn("PySide6.QtQml", spec)
        self.assertIn("PySide6.QtQuick", spec)
        self.assertIn("PySide6.QtQuickControls2", spec)
```

- [ ] **Step 2: Run test to verify red**

Run: `python -m unittest AutoShutdownQt/tests/test_release_packaging.py -v`
Expected: ERROR because `AutoShutdownQt/AutoShutdownQt-2.0.spec` does not exist.

- [ ] **Step 3: Create minimal PyInstaller spec**

Create `AutoShutdownQt/AutoShutdownQt-2.0.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

app_dir = Path(SPECPATH)
qml_dir = app_dir / "qml"

hiddenimports = []
hiddenimports += collect_submodules("PySide6.QtQml")
hiddenimports += collect_submodules("PySide6.QtQuick")
hiddenimports += collect_submodules("PySide6.QtQuickControls2")
hiddenimports += [
    "controller",
    "settings_service",
    "network_service",
    "power_service",
    "script_service",
]

qml_datas = [(str(qml_dir), "qml")]

a = Analysis(
    [str(app_dir / "main.py")],
    pathex=[str(app_dir)],
    binaries=[],
    datas=qml_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AutoShutdownQt",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AutoShutdownQt-2.0",
)
```

- [ ] **Step 4: Run test to verify green**

Run: `python -m unittest AutoShutdownQt/tests/test_release_packaging.py -v`
Expected: PASS.

## Task 3: Release Helper Script

**Files:**
- Modify: `AutoShutdownQt/tests/test_release_packaging.py`
- Create: `AutoShutdownQt/package_release.py`

- [ ] **Step 1: Extend failing script test**

Add to `ReleasePackagingTest`:

```python
PACKAGE_SCRIPT = APP_DIR / "package_release.py"

    def test_release_script_builds_versioned_zip_from_spec(self):
        script = PACKAGE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn('VERSION = "2.0"', script)
        self.assertIn('SPEC_FILE = APP_DIR / "AutoShutdownQt-2.0.spec"', script)
        self.assertIn('DIST_DIR / "AutoShutdownQt-2.0"', script)
        self.assertIn('AutoShutdownQt-2.0.zip', script)
        self.assertIn("PyInstaller", script)
        self.assertIn("zipfile", script)
```

- [ ] **Step 2: Run test to verify red**

Run: `python -m unittest AutoShutdownQt/tests/test_release_packaging.py -v`
Expected: ERROR because `AutoShutdownQt/package_release.py` does not exist.

- [ ] **Step 3: Create release helper**

Create `AutoShutdownQt/package_release.py`:

```python
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

VERSION = "2.0"
APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
SPEC_FILE = APP_DIR / "AutoShutdownQt-2.0.spec"
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build" / "pyinstaller"
APP_BUNDLE_DIR = DIST_DIR / "AutoShutdownQt-2.0"
ZIP_PATH = DIST_DIR / "AutoShutdownQt-2.0.zip"


def run_pyinstaller():
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR),
        str(SPEC_FILE),
    ]
    subprocess.run(command, cwd=ROOT, check=True)


def create_zip():
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(APP_BUNDLE_DIR.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(DIST_DIR))
    return ZIP_PATH


def main():
    run_pyinstaller()
    if not APP_BUNDLE_DIR.exists():
        raise SystemExit(f"Missing build output: {APP_BUNDLE_DIR}")
    zip_path = create_zip()
    print(f"Built AutoShutdownQt {VERSION}: {APP_BUNDLE_DIR}")
    print(f"Created archive: {zip_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify green**

Run: `python -m unittest AutoShutdownQt/tests/test_release_packaging.py -v`
Expected: PASS.

## Task 4: Build and Runtime Verification

**Files:**
- Build output ignored by git: `dist/AutoShutdownQt-2.0/`, `dist/AutoShutdownQt-2.0.zip`, `build/pyinstaller/`

- [ ] **Step 1: Run all code checks**

Run:

```bash
python -m py_compile AutoShutdownQt/main.py AutoShutdownQt/controller.py AutoShutdownQt/power_service.py AutoShutdownQt/script_service.py AutoShutdownQt/settings_service.py AutoShutdownQt/network_service.py AutoShutdownQt/package_release.py
python -m unittest discover AutoShutdownQt/tests -v
```

Expected: all pass.

- [ ] **Step 2: Ensure PyInstaller is available**

Run:

```bash
python -c "import PyInstaller; print(PyInstaller.__version__)"
```

Expected: prints a version. If missing, install with:

```bash
python -m pip install pyinstaller
```

- [ ] **Step 3: Build release artifact**

Run:

```bash
python AutoShutdownQt/package_release.py
```

Expected: creates:

- `dist/AutoShutdownQt-2.0/AutoShutdownQt.exe`
- `dist/AutoShutdownQt-2.0/qml/Main.qml`
- `dist/AutoShutdownQt-2.0.zip`

- [ ] **Step 4: Runtime smoke packaged app**

Run packaged executable with offscreen Qt if supported:

```bash
QT_QPA_PLATFORM=offscreen ./dist/AutoShutdownQt-2.0/AutoShutdownQt.exe
```

Expected: the app starts far enough to load QML. If offscreen executable stays running, stop it after observing no load error. Do not click any live power action outside dry-run.

- [ ] **Step 5: Inspect archive contents**

Run:

```bash
python - <<'PY'
from pathlib import Path
import zipfile
zip_path = Path('dist/AutoShutdownQt-2.0.zip')
with zipfile.ZipFile(zip_path) as zf:
    names = set(zf.namelist())
for required in ['AutoShutdownQt-2.0/AutoShutdownQt.exe', 'AutoShutdownQt-2.0/qml/Main.qml']:
    assert required in names, required
print(zip_path, len(names), 'files')
PY
```

Expected: assertion passes and prints zip summary.

## Task 5: Commit Release Metadata

**Files:**
- Stage: `AutoShutdownQt/main.py`, `AutoShutdownQt/AutoShutdownQt-2.0.spec`, `AutoShutdownQt/package_release.py`, `AutoShutdownQt/tests/test_release_packaging.py`, and this plan.
- Do not stage: `dist/`, `build/`, screenshots, pycache.

- [ ] **Step 1: Check git status**

Run: `git status --short`
Expected: release metadata files modified/untracked; ignored build outputs not shown; two pre-existing screenshots remain untracked.

- [ ] **Step 2: Check staged diff**

Run:

```bash
git add docs/superpowers/plans/2026-06-02-autoshutdown-2-0-release-packaging.md AutoShutdownQt/main.py AutoShutdownQt/AutoShutdownQt-2.0.spec AutoShutdownQt/package_release.py AutoShutdownQt/tests/test_release_packaging.py
git diff --cached --check
git diff --cached --name-only
```

Expected: no whitespace errors; only intended metadata/test/plan files staged.

- [ ] **Step 3: Commit**

Run:

```bash
git commit -m "Prepare AutoShutdownQt 2.0 release packaging"
```

Expected: commit created.

## Self-Review

Spec coverage: version finalization, packaging config, release helper, build artifact, archive inspection, and commit hygiene are covered. Placeholder scan: no TBD/TODO/fill-ins. Type consistency: `VERSION = "2.0"`, `AutoShutdownQt-2.0.spec`, `dist/AutoShutdownQt-2.0`, and `AutoShutdownQt-2.0.zip` match across tests, script, and commands.
