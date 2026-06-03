# AutoShutdownQt 2.0 Local Release Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden AutoShutdownQt 2.0 local release preparation by validating release archives and making small runtime failures visible and safe.

**Architecture:** Keep the existing PySide6/QML architecture intact. `AppController` remains the QML-facing orchestrator, while `package_release.py` gains zip validation helpers. Tests drive each behavior using `unittest`, temp files, and injected controller collaborators so no real power action, GitHub Release, tag, or screenshot cleanup occurs.

**Tech Stack:** Python 3.12+, PySide6, QML, PyInstaller packaging script, Python `unittest`, standard-library `zipfile`/`tempfile`.

---

## Scope Check

The approved spec has two linked release-readiness tracks: local package validation and small runtime reliability hardening. They fit in one plan because each task is independently testable and no new subsystem or UI redesign is introduced. This plan explicitly excludes tag creation, GitHub Release upload, installer work, icon/code-signing work, and deletion of the two untracked screenshot files.

## File Structure

- Modify `AutoShutdownQt/package_release.py`
  - Responsibility: build the PyInstaller app bundle, zip it, then validate expected archive contents before reporting success.
- Modify `AutoShutdownQt/controller.py`
  - Responsibility: keep runtime orchestration safe and visible: timed task replacement, script preflight before live execution, power-action error logging, and process-trigger failure visibility.
- Modify `AutoShutdownQt/tests/test_release_packaging.py`
  - Responsibility: static and functional tests for release packaging script behavior and README release-branch wording.
- Modify `AutoShutdownQt/tests/test_practical_enhancements.py`
  - Responsibility: controller reliability tests for timed task replacement, script preflight, power execution errors, and process-trigger failures.
- Modify `README.md`
  - Responsibility: describe the current local release status from `main` and keep GitHub Release as a separate manual step.

---

### Task 1: Add Local Release Archive Validation

**Files:**
- Modify: `AutoShutdownQt/tests/test_release_packaging.py`
- Modify: `AutoShutdownQt/package_release.py`
- Modify: `README.md`

- [ ] **Step 1: Write failing release validation tests**

Replace `AutoShutdownQt/tests/test_release_packaging.py` with this full file:

```python
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "AutoShutdownQt"
MAIN_PY = APP_DIR / "main.py"
SPEC = APP_DIR / "AutoShutdownQt-2.0.spec"
PACKAGE_SCRIPT = APP_DIR / "package_release.py"
README = ROOT / "README.md"
sys.path.insert(0, str(APP_DIR))

import package_release


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
        self.assertIn("validate_zip_contents", script)

    def test_release_archive_validation_passes_when_exe_and_qml_are_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "AutoShutdownQt-2.0.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("AutoShutdownQt-2.0/AutoShutdownQt.exe", "exe")
                archive.writestr("AutoShutdownQt-2.0/_internal/qml/Main.qml", "qml")

            self.assertTrue(package_release.validate_zip_contents(archive_path))

    def test_release_archive_validation_fails_when_exe_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "AutoShutdownQt-2.0.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("AutoShutdownQt-2.0/_internal/qml/Main.qml", "qml")

            with self.assertRaisesRegex(RuntimeError, "AutoShutdownQt.exe"):
                package_release.validate_zip_contents(archive_path)

    def test_release_archive_validation_fails_when_qml_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "AutoShutdownQt-2.0.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("AutoShutdownQt-2.0/AutoShutdownQt.exe", "exe")

            with self.assertRaisesRegex(RuntimeError, "QML"):
                package_release.validate_zip_contents(archive_path)

    def test_readme_current_release_status_mentions_main_not_old_feature_branch(self):
        readme = README.read_text(encoding="utf-8")
        self.assertIn("main", readme)
        self.assertNotIn("v2-e5e8-reference-ui", readme)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run release packaging tests and verify failure**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_release_packaging -v
```

Expected result: FAIL. At least one failure should mention `validate_zip_contents` missing, and another may mention `v2-e5e8-reference-ui` still present in `README.md`.

- [ ] **Step 3: Implement archive validation in the package script**

Modify `AutoShutdownQt/package_release.py` to include `validate_zip_contents()` and call it from `main()`. The final file should be:

```python
from pathlib import Path
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
APP_BUNDLE_NAME = f"AutoShutdownQt-{VERSION}"
REQUIRED_EXE = f"{APP_BUNDLE_NAME}/AutoShutdownQt.exe"
QML_PREFIXES = (
    f"{APP_BUNDLE_NAME}/_internal/qml/",
    f"{APP_BUNDLE_NAME}/qml/",
)


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


def validate_zip_contents(zip_path=ZIP_PATH):
    target = Path(zip_path)
    if not target.exists():
        raise RuntimeError(f"Missing archive: {target}")

    with zipfile.ZipFile(target, "r") as archive:
        names = set(archive.namelist())

    if not names:
        raise RuntimeError(f"Archive is empty: {target}")

    if REQUIRED_EXE not in names:
        raise RuntimeError(f"Archive is missing required executable: {REQUIRED_EXE}")

    if not any(name.startswith(QML_PREFIXES) for name in names):
        expected = " or ".join(QML_PREFIXES)
        raise RuntimeError(f"Archive is missing required QML resources under: {expected}")

    return True


def main():
    run_pyinstaller()
    if not APP_BUNDLE_DIR.exists():
        raise SystemExit(f"Missing build output: {APP_BUNDLE_DIR}")
    zip_path = create_zip()
    validate_zip_contents(zip_path)
    print(f"Built AutoShutdownQt {VERSION}: {APP_BUNDLE_DIR}")
    print(f"Created archive: {zip_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Update README release status**

In `README.md`, replace the current `## GitHub 发布状态` section with:

```markdown
## GitHub 发布状态

当前 2.0 源码和本地发布准备基线在：

```text
main
```

本仓库提交发布配置和源码，不直接提交本地 zip 包。如需正式 GitHub Release，可在确认 README、测试和本地发布包后创建 `v2.0` tag，并上传 `dist/AutoShutdownQt-2.0.zip`。
```

- [ ] **Step 5: Run release packaging tests and verify pass**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_release_packaging -v
```

Expected result: PASS for all release packaging tests.

- [ ] **Step 6: Commit if explicitly authorized**

Run this only if the user has explicitly authorized commits in the current execution turn:

```bash
git add AutoShutdownQt/package_release.py AutoShutdownQt/tests/test_release_packaging.py README.md
git commit -m "Harden AutoShutdownQt local release packaging"
```

If commit authorization is absent, do not run the commit command and report: `Commit skipped — not authorized.`

---

### Task 2: Make Timed Task Replacement Explicit

**Files:**
- Modify: `AutoShutdownQt/tests/test_practical_enhancements.py`
- Modify: `AutoShutdownQt/controller.py`

- [ ] **Step 1: Add failing timed replacement tests**

Append these tests inside `class PracticalEnhancementsTest(unittest.TestCase)` in `AutoShutdownQt/tests/test_practical_enhancements.py` before the `if __name__ == "__main__":` block:

```python
    def test_starting_new_countdown_replaces_running_timed_task(self):
        controller = AppController()

        controller.startCountdown(0, 10, 0)
        controller.startCountdown(0, 1, 30)

        self.assertEqual(controller.status, "running")
        self.assertEqual(controller.remainingSeconds, 90)
        self.assertEqual(controller.targetInfo, "")
        self.assertIn("已替换上一任务", controller.logText)
        self.assertIn("1 分钟 30 秒", controller.logText)

    def test_starting_fixed_time_replaces_running_countdown(self):
        controller = AppController()

        controller.startCountdown(0, 10, 0)
        controller.startFixedTime(23, 59)

        self.assertEqual(controller.status, "running")
        self.assertIn("23:59", controller.targetInfo)
        self.assertIn("已替换上一任务", controller.logText)
        self.assertIn("已启动定时", controller.logText)
```

- [ ] **Step 2: Run timed replacement tests and verify failure**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_starting_new_countdown_replaces_running_timed_task AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_starting_fixed_time_replaces_running_countdown -v
```

Expected result: FAIL because `已替换上一任务` is not logged yet.

- [ ] **Step 3: Add replacement helper and call it from timed task starters**

In `AutoShutdownQt/controller.py`, add this helper near the private methods before `_on_tick()`:

```python
    def _replace_active_timed_task_if_needed(self):
        if self._status == "running" and self._timer.isActive():
            self._timer.stop()
            self._remaining_seconds = 0
            self._target_time_str = ""
            self._add_log("已替换上一任务")
```

Then modify `startCountdown()` so the body after the invalid-duration guard begins like this:

```python
        self._replace_active_timed_task_if_needed()
        self._remaining_seconds = total
        self._status = "running"
        self._target_time_str = ""
        self._timer.start()
        self._add_log(f"已启动倒计时：{self._format_duration(total)} 后执行 {self.actionLabel}")
        self.statusChanged.emit()
        self.remainingTimeChanged.emit()
        self.targetInfoChanged.emit()
```

Modify `startFixedTime()` so the body after the invalid-delta guard begins like this:

```python
        self._replace_active_timed_task_if_needed()
        self._remaining_seconds = delta
        self._status = "running"
        self._target_time_str = target.strftime("%Y-%m-%d %H:%M")
        self._timer.start()
        self._add_log(f"已启动定时：{self._target_time_str} 执行 {self.actionLabel}")
        self.statusChanged.emit()
        self.remainingTimeChanged.emit()
        self.targetInfoChanged.emit()
```

- [ ] **Step 4: Run timed replacement tests and verify pass**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_starting_new_countdown_replaces_running_timed_task AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_starting_fixed_time_replaces_running_countdown -v
```

Expected result: PASS.

- [ ] **Step 5: Commit if explicitly authorized**

Run this only if the user has explicitly authorized commits in the current execution turn:

```bash
git add AutoShutdownQt/controller.py AutoShutdownQt/tests/test_practical_enhancements.py
git commit -m "Log timed task replacement"
```

If commit authorization is absent, do not run the commit command and report: `Commit skipped — not authorized.`

---

### Task 3: Block Misconfigured Live Scripts and Log Power Failures

**Files:**
- Modify: `AutoShutdownQt/tests/test_practical_enhancements.py`
- Modify: `AutoShutdownQt/controller.py`

- [ ] **Step 1: Add failing script preflight and power failure tests**

Append these tests inside `class PracticalEnhancementsTest(unittest.TestCase)` in `AutoShutdownQt/tests/test_practical_enhancements.py` before the `if __name__ == "__main__":` block:

```python
    def test_live_script_empty_path_blocks_power_without_running_script(self):
        controller = AppController()
        power_calls = []
        controller.dryRun = False
        controller.scriptEnabled = True
        controller.scriptPath = ""
        controller._script_runner = lambda path, timeout: self.fail("script runner should not be called")
        controller._power_executor = lambda action, force: power_calls.append((action, force))

        controller.executeNow()

        self.assertEqual(power_calls, [])
        self.assertIn("脚本路径为空", controller.logText)
        self.assertIn("已阻止电源动作", controller.logText)

    def test_live_script_missing_path_blocks_power_without_running_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            controller = AppController()
            missing_script = Path(tmp) / "missing-before-shutdown.bat"
            power_calls = []
            controller.dryRun = False
            controller.scriptEnabled = True
            controller.scriptPath = str(missing_script)
            controller._script_runner = lambda path, timeout: self.fail("script runner should not be called")
            controller._power_executor = lambda action, force: power_calls.append((action, force))

            controller.executeNow()

            self.assertEqual(power_calls, [])
            self.assertIn("脚本路径不存在", controller.logText)
            self.assertIn("已阻止电源动作", controller.logText)

    def test_power_executor_exception_is_logged_without_propagating(self):
        controller = AppController()
        controller.dryRun = False
        controller.scriptEnabled = False

        def failing_power_executor(action, force):
            raise RuntimeError("power boom")

        controller._power_executor = failing_power_executor

        controller.executeNow()

        self.assertIn("立即执行：执行", controller.logText)
        self.assertIn("电源动作执行失败：power boom", controller.logText)
```

- [ ] **Step 2: Run new script/power tests and verify failure**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_live_script_empty_path_blocks_power_without_running_script AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_live_script_missing_path_blocks_power_without_running_script AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_power_executor_exception_is_logged_without_propagating -v
```

Expected result: FAIL. The empty/missing script tests should fail because the script runner is called, and the power executor test should fail because `RuntimeError("power boom")` propagates.

- [ ] **Step 3: Add script preflight helper**

In `AutoShutdownQt/controller.py`, add this helper near `_execute_with_script()`:

```python
    def _validate_script_before_real_execution(self):
        clean_path = self._script_path.strip()
        if not clean_path:
            self._add_log("脚本路径为空，已阻止电源动作")
            return False
        path = Path(clean_path).expanduser()
        if not path.exists():
            self._add_log(f"脚本路径不存在，已阻止电源动作：{path}")
            return False
        return True
```

Then replace the script-enabled real-mode branch inside `_execute_with_script()` with this exact block:

```python
        if self._script_enabled:
            if self._dry_run:
                self._add_log(f"Dry-run：将执行脚本 {self._script_path or '(未设置路径)'}")
            else:
                if not self._validate_script_before_real_execution():
                    return
                result = self._script_runner(self._script_path, self._script_timeout_seconds)
                self._add_log(result.message)
                if not result.ok:
                    self._add_log("脚本失败，已阻止电源动作")
                    return
```

- [ ] **Step 4: Catch and log power execution exceptions**

In `AutoShutdownQt/controller.py`, replace the last two lines of `_execute_with_script()`:

```python
        self._add_log(f"{reason}：执行 {self.actionLabel}")
        self._execute_power_action()
```

with:

```python
        self._add_log(f"{reason}：执行 {self.actionLabel}")
        try:
            self._execute_power_action()
        except Exception as exc:
            self._add_log(f"电源动作执行失败：{exc}")
```

- [ ] **Step 5: Run script/power tests and verify pass**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_live_script_empty_path_blocks_power_without_running_script AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_live_script_missing_path_blocks_power_without_running_script AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_power_executor_exception_is_logged_without_propagating -v
```

Expected result: PASS.

- [ ] **Step 6: Commit if explicitly authorized**

Run this only if the user has explicitly authorized commits in the current execution turn:

```bash
git add AutoShutdownQt/controller.py AutoShutdownQt/tests/test_practical_enhancements.py
git commit -m "Block misconfigured live scripts"
```

If commit authorization is absent, do not run the commit command and report: `Commit skipped — not authorized.`

---

### Task 4: Make Process Trigger Detection Failures Visible

**Files:**
- Modify: `AutoShutdownQt/tests/test_practical_enhancements.py`
- Modify: `AutoShutdownQt/controller.py`

- [ ] **Step 1: Add failing process detection failure tests**

Append these tests inside `class PracticalEnhancementsTest(unittest.TestCase)` in `AutoShutdownQt/tests/test_practical_enhancements.py` before the `if __name__ == "__main__":` block:

```python
    def test_process_trigger_checker_exception_fails_closed_on_start(self):
        controller = AppController()
        power_calls = []
        controller.processName = "demo.exe"
        controller._power_executor = lambda action, force: power_calls.append((action, force))

        def failing_checker(name):
            raise RuntimeError("tasklist boom")

        controller._process_checker = failing_checker

        controller.startProcessTrigger()

        self.assertFalse(controller.processTriggerActive)
        self.assertEqual(power_calls, [])
        self.assertIn("进程检测失败", controller.processTriggerStatus)
        self.assertIn("tasklist boom", controller.logText)

    def test_process_trigger_checker_exception_fails_closed_during_poll(self):
        controller = AppController()
        power_calls = []
        controller.processName = "demo.exe"
        controller._power_executor = lambda action, force: power_calls.append((action, force))
        calls = {"count": 0}

        def checker(name):
            calls["count"] += 1
            if calls["count"] == 1:
                return True
            raise RuntimeError("poll boom")

        controller._process_checker = checker

        controller.startProcessTrigger()
        controller._poll_process_trigger()

        self.assertFalse(controller.processTriggerActive)
        self.assertEqual(power_calls, [])
        self.assertIn("进程检测失败", controller.processTriggerStatus)
        self.assertIn("poll boom", controller.logText)
```

- [ ] **Step 2: Run process detection failure tests and verify failure**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_process_trigger_checker_exception_fails_closed_on_start AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_process_trigger_checker_exception_fails_closed_during_poll -v
```

Expected result: FAIL because checker exceptions currently propagate or become invisible.

- [ ] **Step 3: Add process check error state in the controller constructor**

In `AutoShutdownQt/controller.py`, inside `__init__()` after this line:

```python
        self._process_checker = self._is_process_running
```

add:

```python
        self._last_process_check_error = ""
```

- [ ] **Step 4: Add process check wrapper helper**

In `AutoShutdownQt/controller.py`, add this helper before `_is_process_running()`:

```python
    def _check_process_running(self, process_name):
        self._last_process_check_error = ""
        try:
            return bool(self._process_checker(process_name))
        except Exception as exc:
            self._last_process_check_error = str(exc)
            return False
```

- [ ] **Step 5: Use the wrapper when starting the process trigger**

In `AutoShutdownQt/controller.py`, replace this line in `startProcessTrigger()`:

```python
        self._process_seen = bool(self._process_checker(name))
```

with this block:

```python
        self._process_seen = self._check_process_running(name)
        if self._last_process_check_error:
            self._process_trigger_active = False
            self._process_seen = False
            self._process_trigger_status = f"进程检测失败：{self._last_process_check_error}"
            self._add_log(f"进程退出触发未启动：{self._process_trigger_status}")
            self.processTriggerChanged.emit()
            return
```

- [ ] **Step 6: Use the wrapper when polling the process trigger**

In `AutoShutdownQt/controller.py`, replace this line in `_poll_process_trigger()`:

```python
        running = bool(self._process_checker(name))
```

with this block:

```python
        running = self._check_process_running(name)
        if self._last_process_check_error:
            self._process_timer.stop()
            self._process_trigger_active = False
            self._process_seen = False
            self._process_trigger_status = f"进程检测失败：{self._last_process_check_error}"
            self._add_log(f"进程退出触发已停止：{self._process_trigger_status}")
            self.processTriggerChanged.emit()
            return
```

- [ ] **Step 7: Make built-in tasklist errors visible to the wrapper**

In `AutoShutdownQt/controller.py`, replace the exception handler in `_is_process_running()`:

```python
        except Exception:
            return False
```

with:

```python
        except Exception as exc:
            self._last_process_check_error = str(exc)
            return False
```

- [ ] **Step 8: Run process detection failure tests and verify pass**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_process_trigger_checker_exception_fails_closed_on_start AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_process_trigger_checker_exception_fails_closed_during_poll -v
```

Expected result: PASS.

- [ ] **Step 9: Commit if explicitly authorized**

Run this only if the user has explicitly authorized commits in the current execution turn:

```bash
git add AutoShutdownQt/controller.py AutoShutdownQt/tests/test_practical_enhancements.py
git commit -m "Surface process trigger failures"
```

If commit authorization is absent, do not run the commit command and report: `Commit skipped — not authorized.`

---

### Task 5: Full Verification and Release Readiness Check

**Files:**
- Verify: `AutoShutdownQt/main.py`
- Verify: `AutoShutdownQt/controller.py`
- Verify: `AutoShutdownQt/power_service.py`
- Verify: `AutoShutdownQt/script_service.py`
- Verify: `AutoShutdownQt/settings_service.py`
- Verify: `AutoShutdownQt/network_service.py`
- Verify: `AutoShutdownQt/package_release.py`
- Verify: `AutoShutdownQt/tests/`

- [ ] **Step 1: Run Python compile checks**

Run:

```bash
python -m py_compile AutoShutdownQt/main.py AutoShutdownQt/controller.py AutoShutdownQt/power_service.py AutoShutdownQt/script_service.py AutoShutdownQt/settings_service.py AutoShutdownQt/network_service.py AutoShutdownQt/package_release.py
```

Expected result: command exits 0 with no output.

- [ ] **Step 2: Run the full unit test suite**

Run:

```bash
python -m unittest discover AutoShutdownQt/tests -v
```

Expected result: all tests pass. The previous baseline was 28 tests; this plan adds 10 tests, so the expected total is 38 tests unless existing tests are split by the executor.

- [ ] **Step 3: Check working tree without touching screenshots**

Run:

```bash
git status --short
```

Expected result: modified files should include only planned files plus the spec/plan documents. The existing untracked screenshot files may still appear:

```text
?? AutoShutdownQt/current-render.png
?? AutoShutdownQt/e5e8b88f-7acc-4be7-930f-952ad1670984.png
```

Do not add, delete, or rename those screenshot files.

- [ ] **Step 4: Run local package script when PyInstaller is available**

Run:

```bash
python AutoShutdownQt/package_release.py
```

Expected result when PyInstaller and PySide6 packaging dependencies are installed:

```text
Built AutoShutdownQt 2.0: .../dist/AutoShutdownQt-2.0
Created archive: .../dist/AutoShutdownQt-2.0.zip
```

If the command fails because PyInstaller is not installed, record the exact error and do not install packages unless the user explicitly asks.

- [ ] **Step 5: Commit final verification state if explicitly authorized**

Run this only if the user has explicitly authorized commits in the current execution turn and prior task commits were skipped:

```bash
git add AutoShutdownQt/controller.py AutoShutdownQt/package_release.py AutoShutdownQt/tests/test_practical_enhancements.py AutoShutdownQt/tests/test_release_packaging.py README.md docs/superpowers/specs/2026-06-02-autoshutdown-local-release-hardening-design.md docs/superpowers/plans/2026-06-02-autoshutdown-local-release-hardening.md
git commit -m "Harden AutoShutdownQt 2.0 local release readiness"
```

If commit authorization is absent, do not run the commit command and report: `Commit skipped — not authorized.`

---

## Self-Review

- Spec coverage: local release validation is covered by Task 1; README branch correction is covered by Task 1; timed task replacement is covered by Task 2; live script preflight and power failure logging are covered by Task 3; process-trigger failure visibility is covered by Task 4; compile, unit tests, package script, and screenshot preservation are covered by Task 5.
- Placeholder scan: this plan contains concrete file paths, exact commands, exact code snippets, and expected results for every task.
- Type consistency: controller methods use existing `AppController` attributes (`_timer`, `_status`, `_script_path`, `_process_checker`, `_power_executor`) and existing `unittest` patterns from the repository. Package validation uses standard `Path` and `zipfile` types already imported by `package_release.py`.
