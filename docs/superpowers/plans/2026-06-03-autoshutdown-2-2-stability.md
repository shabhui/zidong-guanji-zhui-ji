# AutoShutdownQt 2.2 Stability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build AutoShutdownQt 2.2 as a focused stability patch for 2.1 queue, tray, and release behavior.

**Architecture:** Keep the existing 2.1 boundaries: `TaskScheduler` owns persisted queue state, `AppController` coordinates QML and runtime trigger monitors, `TrayService` delegates tray callbacks, and `package_release.py` builds release artifacts. Add small controller helpers for trigger queue synchronization instead of introducing a new module.

**Tech Stack:** Python 3.12, PySide6/QML, unittest, PyInstaller, GitHub release artifacts.

---

## File Structure

- `AutoShutdownQt/task_scheduler.py` — queue state, task ordering, serialization, due-task calculation, loaded-task normalization.
- `AutoShutdownQt/controller.py` — QML bridge, process/network monitor lifecycle, queue synchronization, tray quit coordination.
- `AutoShutdownQt/tray_service.py` — tray menu callbacks and tray availability reporting.
- `AutoShutdownQt/qml/Main.qml` — user-facing copy for close-to-tray and tray availability expectations.
- `AutoShutdownQt/package_release.py` — versioned packaging constants, checksum, checklist, manifest validation.
- `AutoShutdownQt/AutoShutdownQt-2.2.spec` — PyInstaller spec for 2.2.
- `.gitignore` — allow 2.2 spec to be committed.
- `README.md` — current release and checksum notes.
- `RELEASE_NOTES_v2.2.md` — v2.2 release notes.
- `AutoShutdownQt/tests/test_task_scheduler.py` — scheduler startup normalization tests.
- `AutoShutdownQt/tests/test_practical_enhancements.py` — controller queue/trigger synchronization tests.
- `AutoShutdownQt/tests/test_tray_service.py` — tray callback and availability behavior tests.
- `AutoShutdownQt/tests/test_e5e8_ui_regressions.py` — QML copy/static wiring tests.
- `AutoShutdownQt/tests/test_release_packaging.py` — 2.2 packaging identity and release artifact tests.

---

### Task 1: Scheduler startup normalization for recurring tasks

**Files:**
- Modify: `AutoShutdownQt/task_scheduler.py`
- Modify: `AutoShutdownQt/tests/test_task_scheduler.py`

- [ ] **Step 1: Write failing scheduler tests**

Append these tests inside `TaskSchedulerTest` in `AutoShutdownQt/tests/test_task_scheduler.py`:

```python
    def test_load_recomputes_recurring_fixed_time_next_run_even_when_saved_stale(self):
        scheduler = TaskScheduler(now_provider=lambda: datetime(2026, 6, 3, 12, 0, 0))
        saved = {
            "version": 1,
            "tasks": [{
                "id": "daily-1",
                "name": "每天睡眠",
                "action": "sleep",
                "forceClose": False,
                "triggerType": "fixed_time",
                "triggerConfig": {"hour": 8, "minute": 30},
                "repeatRule": "daily",
                "enabled": True,
                "status": "pending",
                "createdOrder": 1,
                "nextRunAt": "2026-06-02T08:30:00",
                "lastRunAt": None,
                "lastError": "",
            }],
        }

        scheduler.load_from_settings(saved)

        task = scheduler.tasks[0]
        self.assertEqual(task.next_run_at, datetime(2026, 6, 4, 8, 30, 0))
        self.assertEqual(scheduler.due_tasks(datetime(2026, 6, 3, 12, 0, 0)), [])

    def test_load_keeps_disabled_recurring_fixed_time_paused(self):
        scheduler = TaskScheduler(now_provider=lambda: datetime(2026, 6, 3, 12, 0, 0))
        saved = {
            "version": 1,
            "tasks": [{
                "id": "daily-paused",
                "name": "暂停每日任务",
                "action": "sleep",
                "forceClose": False,
                "triggerType": "fixed_time",
                "triggerConfig": {"hour": 8, "minute": 30},
                "repeatRule": "daily",
                "enabled": False,
                "status": "pending",
                "createdOrder": 1,
                "nextRunAt": "2026-06-02T08:30:00",
                "lastRunAt": None,
                "lastError": "",
            }],
        }

        scheduler.load_from_settings(saved)

        task = scheduler.tasks[0]
        self.assertIsNone(task.next_run_at)
        self.assertEqual(task.status.value, "paused")
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_task_scheduler.TaskSchedulerTest.test_load_recomputes_recurring_fixed_time_next_run_even_when_saved_stale AutoShutdownQt.tests.test_task_scheduler.TaskSchedulerTest.test_load_keeps_disabled_recurring_fixed_time_paused -v
```

Expected: first test FAILS because stale saved `nextRunAt` is preserved; second test should PASS or remain PASS.

- [ ] **Step 3: Implement minimal scheduler normalization**

Modify `TaskScheduler._normalize_loaded_task()` in `AutoShutdownQt/task_scheduler.py` to this:

```python
    def _normalize_loaded_task(self, task):
        if not task.enabled:
            task.status = TaskStatus.PAUSED
            task.next_run_at = None
        elif task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            task.next_run_at = None
        elif task.trigger_type == TaskTriggerType.FIXED_TIME and task.repeat_rule != RepeatRule.ONCE:
            task.status = TaskStatus.PENDING
            self._schedule_next_run(task, self._now_provider())
        elif task.next_run_at is None:
            self._schedule_next_run(task, self._now_provider())
```

- [ ] **Step 4: Run scheduler tests**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_task_scheduler -v
```

Expected: PASS.

- [ ] **Step 5: Commit scheduler normalization**

```bash
git add AutoShutdownQt/task_scheduler.py AutoShutdownQt/tests/test_task_scheduler.py
git commit -m "$(cat <<'EOF'
Stabilize recurring task startup scheduling
EOF
)"
```

---

### Task 2: Process trigger queue synchronization

**Files:**
- Modify: `AutoShutdownQt/controller.py`
- Modify: `AutoShutdownQt/tests/test_practical_enhancements.py`

- [ ] **Step 1: Write failing process trigger synchronization tests**

Append these tests inside `PracticalEnhancementsTest` in `AutoShutdownQt/tests/test_practical_enhancements.py`:

```python
    def test_starting_second_process_trigger_replaces_previous_process_queue_task(self):
        controller = AppController()
        controller._process_checker = lambda name: True

        controller.processName = "first.exe"
        controller.startProcessTrigger()
        controller.processName = "second.exe"
        controller.startProcessTrigger()

        self.assertEqual(controller.queueTaskCount, 1)
        self.assertNotIn("first.exe", controller.queueText)
        self.assertIn("second.exe", controller.queueText)

    def test_stopping_process_trigger_removes_matching_queue_task(self):
        controller = AppController()
        controller.processName = "demo.exe"
        controller._process_checker = lambda name: True

        controller.startProcessTrigger()
        controller.stopProcessTrigger()

        self.assertFalse(controller.processTriggerActive)
        self.assertNotIn("process_exit", controller.queueRowsJson)
        self.assertEqual(controller.queueTaskCount, 0)

    def test_deleting_active_process_queue_task_stops_process_monitor(self):
        controller = AppController()
        controller.processName = "demo.exe"
        controller._process_checker = lambda name: True
        controller.startProcessTrigger()
        task_id = controller._scheduler.tasks[0].id

        controller.deleteQueueTask(task_id)

        self.assertFalse(controller.processTriggerActive)
        self.assertEqual(controller.processTriggerStatus, "已停止")
        self.assertEqual(controller.queueTaskCount, 0)
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_starting_second_process_trigger_replaces_previous_process_queue_task AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_stopping_process_trigger_removes_matching_queue_task AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_deleting_active_process_queue_task_stops_process_monitor -v
```

Expected: FAIL because process trigger queue rows are not replaced or removed.

- [ ] **Step 3: Add trigger queue helper methods**

Add these helper methods in `AutoShutdownQt/controller.py` before `_execute_task()`:

```python
    def _queue_tasks_by_trigger(self, trigger_type):
        return [task for task in self._scheduler.tasks if task.trigger_type == trigger_type]

    def _remove_queue_tasks_by_trigger(self, trigger_type):
        removed = False
        for task in self._queue_tasks_by_trigger(trigger_type):
            removed = self._scheduler.remove_task(task.id) or removed
        return removed

    def _stop_process_monitor_without_queue_update(self):
        self._process_timer.stop()
        self._process_trigger_active = False
        self._process_seen = False
        self._process_target_name = ""
        self._process_trigger_status = "已停止"

    def _stop_network_monitor_without_queue_update(self):
        self._network_timer.stop()
        self._network_trigger_active = False
        self._network_idle_elapsed = 0.0
        self._network_previous_sample = None
        self._network_trigger_status = "已停止"
```

- [ ] **Step 4: Update process start/stop/delete paths**

In `startProcessTrigger()`, immediately before `self._scheduler.add_task(...)`, add:

```python
        if self._remove_queue_tasks_by_trigger(TaskTriggerType.PROCESS_EXIT):
            self._add_log("已替换上一进程退出队列任务")
```

Replace `stopProcessTrigger()` body with:

```python
    @Slot()
    def stopProcessTrigger(self):
        self._stop_process_monitor_without_queue_update()
        self._remove_queue_tasks_by_trigger(TaskTriggerType.PROCESS_EXIT)
        self._save_settings()
        self._add_log("进程退出触发已停止")
        self.taskQueueChanged.emit()
        self.processTriggerChanged.emit()
```

Modify `deleteQueueTask()` so it fetches the task before removing it:

```python
    @Slot(str)
    def deleteQueueTask(self, task_id):
        try:
            task = self._scheduler.get_task(task_id)
        except KeyError:
            self._add_log(f"任务不存在：{task_id}")
            return
        if task.trigger_type == TaskTriggerType.PROCESS_EXIT:
            self._stop_process_monitor_without_queue_update()
            self.processTriggerChanged.emit()
        elif task.trigger_type == TaskTriggerType.NETWORK_IDLE:
            self._stop_network_monitor_without_queue_update()
            self.networkTriggerChanged.emit()
        self._scheduler.remove_task(task_id)
        self._save_settings()
        self._add_log("任务已删除")
        self.taskQueueChanged.emit()
```

- [ ] **Step 5: Run process synchronization tests**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_starting_second_process_trigger_replaces_previous_process_queue_task AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_stopping_process_trigger_removes_matching_queue_task AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_deleting_active_process_queue_task_stops_process_monitor -v
```

Expected: PASS.

- [ ] **Step 6: Commit process synchronization**

```bash
git add AutoShutdownQt/controller.py AutoShutdownQt/tests/test_practical_enhancements.py
git commit -m "$(cat <<'EOF'
Synchronize process triggers with queue tasks
EOF
)"
```

---

### Task 3: Network trigger queue synchronization

**Files:**
- Modify: `AutoShutdownQt/controller.py`
- Modify: `AutoShutdownQt/tests/test_practical_enhancements.py`

- [ ] **Step 1: Write failing network trigger synchronization tests**

Append these tests inside `PracticalEnhancementsTest`:

```python
    def test_starting_second_network_trigger_replaces_previous_network_queue_task(self):
        samples = [
            NetworkSample(True, received_bytes=1, sent_bytes=1, monotonic_seconds=1.0),
            NetworkSample(True, received_bytes=2, sent_bytes=2, monotonic_seconds=2.0),
        ]
        controller = AppController(network_reader=FakeNetworkReader(samples))

        controller.networkIdleSeconds = 60
        controller.startNetworkTrigger()
        controller.networkIdleSeconds = 120
        controller.startNetworkTrigger()

        self.assertEqual(controller.queueTaskCount, 1)
        self.assertIn("网络闲置 120 秒", controller.queueText)

    def test_stopping_network_trigger_removes_matching_queue_task(self):
        samples = [NetworkSample(True, received_bytes=1, sent_bytes=1, monotonic_seconds=1.0)]
        controller = AppController(network_reader=FakeNetworkReader(samples))

        controller.startNetworkTrigger()
        controller.stopNetworkTrigger()

        self.assertFalse(controller.networkTriggerActive)
        self.assertNotIn("network_idle", controller.queueRowsJson)
        self.assertEqual(controller.queueTaskCount, 0)

    def test_deleting_active_network_queue_task_stops_network_monitor(self):
        samples = [NetworkSample(True, received_bytes=1, sent_bytes=1, monotonic_seconds=1.0)]
        controller = AppController(network_reader=FakeNetworkReader(samples))
        controller.startNetworkTrigger()
        task_id = controller._scheduler.tasks[0].id

        controller.deleteQueueTask(task_id)

        self.assertFalse(controller.networkTriggerActive)
        self.assertEqual(controller.networkTriggerStatus, "已停止")
        self.assertEqual(controller.queueTaskCount, 0)
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_starting_second_network_trigger_replaces_previous_network_queue_task AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_stopping_network_trigger_removes_matching_queue_task AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_deleting_active_network_queue_task_stops_network_monitor -v
```

Expected: FAIL because network trigger queue rows are not replaced or removed.

- [ ] **Step 3: Update network start/stop paths**

In `startNetworkTrigger()`, immediately before `self._scheduler.add_task(...)`, add:

```python
        if self._remove_queue_tasks_by_trigger(TaskTriggerType.NETWORK_IDLE):
            self._add_log("已替换上一网络闲置队列任务")
```

Replace `stopNetworkTrigger()` body with:

```python
    @Slot()
    def stopNetworkTrigger(self):
        self._stop_network_monitor_without_queue_update()
        self._remove_queue_tasks_by_trigger(TaskTriggerType.NETWORK_IDLE)
        self._save_settings()
        self._add_log("网络闲置触发已停止")
        self.taskQueueChanged.emit()
        self.networkTriggerChanged.emit()
```

- [ ] **Step 4: Run network synchronization tests**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_starting_second_network_trigger_replaces_previous_network_queue_task AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_stopping_network_trigger_removes_matching_queue_task AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_deleting_active_network_queue_task_stops_network_monitor -v
```

Expected: PASS.

- [ ] **Step 5: Run practical enhancement regression tests**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements -v
```

Expected: PASS.

- [ ] **Step 6: Commit network synchronization**

```bash
git add AutoShutdownQt/controller.py AutoShutdownQt/tests/test_practical_enhancements.py
git commit -m "$(cat <<'EOF'
Synchronize network triggers with queue tasks
EOF
)"
```

---

### Task 4: Tray quit and unavailable-tray copy

**Files:**
- Modify: `AutoShutdownQt/controller.py`
- Modify: `AutoShutdownQt/qml/Main.qml`
- Modify: `AutoShutdownQt/tests/test_e5e8_ui_regressions.py`
- Modify: `AutoShutdownQt/tests/test_tray_service.py`

- [ ] **Step 1: Write failing QML copy regression test**

Append this test inside `E5E8ButtonRegressionTest` in `AutoShutdownQt/tests/test_e5e8_ui_regressions.py`:

```python
    def test_2_2_tray_copy_mentions_availability_and_explicit_quit(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertIn("托盘可用时关闭窗口会隐藏到后台", main)
        self.assertIn("托盘不可用时关闭窗口不会继续后台运行", main)
        self.assertIn("托盘菜单 Quit", main)
        self.assertIn("trayCloseRequested", main)
        self.assertIn("mainWindow.hide()", main)
```

- [ ] **Step 2: Run QML test and verify failure**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_e5e8_ui_regressions.E5E8ButtonRegressionTest.test_2_2_tray_copy_mentions_availability_and_explicit_quit -v
```

Expected: FAIL because the exact v2.2 copy is absent.

- [ ] **Step 3: Write tray service callback regression test**

Append this test inside `TrayServiceTest` in `AutoShutdownQt/tests/test_tray_service.py`:

```python
    def test_quit_app_marks_window_for_explicit_quit_when_property_exists(self):
        window = FakeWindow()
        window.trayCloseRequested = False
        controller = FakeController()
        service = TrayService(controller, window, tray_factory=lambda: object())

        service.quit_app()

        self.assertTrue(window.trayCloseRequested)
        self.assertTrue(controller.quit_requested)
```

- [ ] **Step 4: Run tray test and verify failure**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_tray_service.TrayServiceTest.test_quit_app_marks_window_for_explicit_quit_when_property_exists -v
```

Expected: FAIL because `TrayService.quit_app()` does not set `trayCloseRequested`.

- [ ] **Step 5: Implement tray quit marker**

Modify `TrayService.quit_app()` in `AutoShutdownQt/tray_service.py`:

```python
    def quit_app(self):
        if hasattr(self._window, "trayCloseRequested"):
            self._window.trayCloseRequested = True
        self._controller.requestQuit()
```

- [ ] **Step 6: Update settings copy**

In `AutoShutdownQt/qml/Main.qml`, replace the settings safety text with:

```qml
                        text: "LIVE MODE 会执行真实系统动作。建议验证时保持 Dry-run 开启；立即执行按钮会再次弹窗确认，倒计时和进程/网络触发到点后不会再次确认。托盘可用时关闭窗口会隐藏到后台；托盘不可用时关闭窗口不会继续后台运行。请使用托盘菜单 Quit 显式退出。"
```

- [ ] **Step 7: Run tray and QML tests**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_tray_service AutoShutdownQt.tests.test_e5e8_ui_regressions -v
```

Expected: PASS.

- [ ] **Step 8: Commit tray stability copy**

```bash
git add AutoShutdownQt/tray_service.py AutoShutdownQt/qml/Main.qml AutoShutdownQt/tests/test_tray_service.py AutoShutdownQt/tests/test_e5e8_ui_regressions.py
git commit -m "$(cat <<'EOF'
Clarify tray quit behavior for AutoShutdownQt 2.2
EOF
)"
```

---

### Task 5: Release packaging identity for 2.2

**Files:**
- Create: `AutoShutdownQt/AutoShutdownQt-2.2.spec`
- Modify: `.gitignore`
- Modify: `AutoShutdownQt/main.py`
- Modify: `AutoShutdownQt/package_release.py`
- Modify: `AutoShutdownQt/tests/test_release_packaging.py`

- [ ] **Step 1: Write failing packaging tests**

Append these tests inside `ReleasePackagingTest` in `AutoShutdownQt/tests/test_release_packaging.py`:

```python
    def test_main_declares_final_2_2_version(self):
        main = MAIN_PY.read_text(encoding="utf-8")
        self.assertIn('app.setApplicationVersion("2.2")', main)

    def test_release_script_builds_2_2_artifacts(self):
        script = PACKAGE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn('VERSION = "2.2"', script)
        self.assertIn('AutoShutdownQt-2.2.spec', script)
        self.assertIn('AutoShutdownQt-2.2.zip', script)
        self.assertIn('release-checklist-v2.2.md', script)

    def test_release_checklist_mentions_tray_queue_and_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            checklist = package_release.create_release_checklist(Path(tmp) / "release-checklist-v2.2.md")
            content = checklist.read_text(encoding="utf-8")

            self.assertIn("tray Quit", content)
            self.assertIn("queue persistence", content)
            self.assertIn("close-to-tray", content)
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_release_packaging.ReleasePackagingTest.test_main_declares_final_2_2_version AutoShutdownQt.tests.test_release_packaging.ReleasePackagingTest.test_release_script_builds_2_2_artifacts AutoShutdownQt.tests.test_release_packaging.ReleasePackagingTest.test_release_checklist_mentions_tray_queue_and_persistence -v
```

Expected: FAIL because package identity is still 2.1.

- [ ] **Step 3: Create 2.2 PyInstaller spec**

Create `AutoShutdownQt/AutoShutdownQt-2.2.spec` by copying `AutoShutdownQt/AutoShutdownQt-2.1.spec` and changing only the final `COLLECT(... name=...)` value:

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
    "task_model",
    "task_scheduler",
    "tray_service",
    "PySide6.QtWidgets",
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
    name="AutoShutdownQt-2.2",
)
```

- [ ] **Step 4: Update version constants**

Modify these values:

In `AutoShutdownQt/main.py`:

```python
    app.setApplicationVersion("2.2")
```

In `AutoShutdownQt/package_release.py`:

```python
VERSION = "2.2"
SPEC_FILE = APP_DIR / "AutoShutdownQt-2.2.spec"
APP_BUNDLE_DIR = DIST_DIR / "AutoShutdownQt-2.2"
ZIP_PATH = DIST_DIR / "AutoShutdownQt-2.2.zip"
RELEASE_CHECKLIST_PATH = DIST_DIR / "release-checklist-v2.2.md"
```

In `.gitignore`, add:

```gitignore
!AutoShutdownQt/AutoShutdownQt-2.2.spec
```

- [ ] **Step 5: Update checklist content**

Modify `create_release_checklist()` in `AutoShutdownQt/package_release.py`:

```python
def create_release_checklist(target_path=RELEASE_CHECKLIST_PATH):
    target = Path(target_path)
    target.write_text(
        "# AutoShutdownQt 2.2 Release Checklist\n\n"
        "- [ ] Launch app with Dry-run enabled by default.\n"
        "- [ ] Verify countdown task logs dry-run output only.\n"
        "- [ ] Verify fixed-time daily/weekday/weekend tasks compute next run.\n"
        "- [ ] Verify process/network trigger rows stay synchronized with monitors.\n"
        "- [ ] Verify queue persistence across restart.\n"
        "- [ ] Verify close-to-tray behavior when tray is available.\n"
        "- [ ] Verify tray Quit exits explicitly.\n"
        "- [ ] Do not execute real shutdown, restart, sleep, hibernate, logoff, or lock during validation.\n"
        "- [ ] Publish SHA256SUMS.txt next to the zip.\n",
        encoding="utf-8",
    )
    return target
```

- [ ] **Step 6: Run packaging tests**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_release_packaging -v
```

Expected: PASS.

- [ ] **Step 7: Commit 2.2 packaging identity**

```bash
git add .gitignore AutoShutdownQt/main.py AutoShutdownQt/package_release.py AutoShutdownQt/AutoShutdownQt-2.2.spec AutoShutdownQt/tests/test_release_packaging.py
git commit -m "$(cat <<'EOF'
Prepare AutoShutdownQt 2.2 release packaging
EOF
)"
```

---

### Task 6: 2.2 release docs

**Files:**
- Create: `RELEASE_NOTES_v2.2.md`
- Modify: `README.md`
- Modify: `AutoShutdownQt/tests/test_release_packaging.py`

- [ ] **Step 1: Write failing docs tests**

Append these tests inside `ReleasePackagingTest`:

```python
    def test_release_notes_document_2_2_stability_patch(self):
        notes = (ROOT / "RELEASE_NOTES_v2.2.md").read_text(encoding="utf-8")
        self.assertIn("2.2", notes)
        self.assertIn("stability", notes.lower())
        self.assertIn("queue", notes.lower())
        self.assertIn("tray", notes.lower())
        self.assertIn("SHA256SUMS.txt", notes)

    def test_readme_mentions_2_2_download_and_checksum(self):
        readme = README.read_text(encoding="utf-8")
        self.assertIn("AutoShutdownQt 2.2", readme)
        self.assertIn("AutoShutdownQt-2.2.zip", readme)
        self.assertIn("SHA256SUMS.txt", readme)
```

- [ ] **Step 2: Run docs tests and verify failure**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_release_packaging.ReleasePackagingTest.test_release_notes_document_2_2_stability_patch AutoShutdownQt.tests.test_release_packaging.ReleasePackagingTest.test_readme_mentions_2_2_download_and_checksum -v
```

Expected: FAIL because v2.2 docs are absent.

- [ ] **Step 3: Create v2.2 release notes**

Create `RELEASE_NOTES_v2.2.md`:

```markdown
# AutoShutdownQt 2.2 Release Notes

AutoShutdownQt 2.2 is a stability patch for the 2.1 practical scheduler release.

## Release artifacts

- Portable directory: `dist/AutoShutdownQt-2.2/`
- Portable zip: `dist/AutoShutdownQt-2.2.zip`
- Checksum file: `dist/SHA256SUMS.txt`
- Release checklist: `dist/release-checklist-v2.2.md`

## Stability fixes

- Queue rows stay synchronized with process and network trigger monitors.
- Starting a new process or network trigger replaces the previous active trigger row.
- Stopping or deleting trigger rows stops the matching runtime monitor.
- Recurring fixed-time tasks recompute their next run on startup instead of trusting stale saved timestamps.
- Tray Quit explicitly exits instead of behaving like close-to-tray.

## Safety notes

- Dry-run remains enabled by default.
- Do not execute real shutdown, restart, sleep, hibernate, logoff, or lock during validation.
- The portable exe is not code signed.
```

- [ ] **Step 4: Update README release section**

In `README.md`, add or update a release section to include this text:

```markdown
## Current release

AutoShutdownQt 2.2 is the current stability release.

- Download: `AutoShutdownQt-2.2.zip`
- Verify checksum with `SHA256SUMS.txt`
- Dry-run is enabled by default.
- Close-to-tray depends on tray availability; use tray Quit for explicit exit.
```

Do not remove existing build/test instructions unless they conflict with the current release identity.

- [ ] **Step 5: Run docs tests**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_release_packaging.ReleasePackagingTest.test_release_notes_document_2_2_stability_patch AutoShutdownQt.tests.test_release_packaging.ReleasePackagingTest.test_readme_mentions_2_2_download_and_checksum -v
```

Expected: PASS.

- [ ] **Step 6: Commit docs**

```bash
git add README.md RELEASE_NOTES_v2.2.md AutoShutdownQt/tests/test_release_packaging.py
git commit -m "$(cat <<'EOF'
Document AutoShutdownQt 2.2 stability release
EOF
)"
```

---

### Task 7: Full verification and package smoke check

**Files:**
- No code changes expected.

- [ ] **Step 1: Run full test suite**

Run:

```bash
python -m unittest discover AutoShutdownQt/tests -v
```

Expected: PASS, with all tests green.

- [ ] **Step 2: Build release package**

Run:

```bash
python AutoShutdownQt/package_release.py
```

Expected: creates:

```text
dist/AutoShutdownQt-2.2/
dist/AutoShutdownQt-2.2.zip
dist/SHA256SUMS.txt
dist/release-checklist-v2.2.md
```

PyInstaller may print a QML plugin logging warning. That warning is acceptable only if the command exits successfully and the zip/checksum/checklist are created.

- [ ] **Step 3: Validate package artifacts with tests**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_release_packaging -v
```

Expected: PASS.

- [ ] **Step 4: Check git status**

Run:

```bash
git status --short
```

Expected: clean, or only ignored build artifacts under `dist/` and `build/`.

- [ ] **Step 5: Push branch**

Run:

```bash
git push
```

Expected: branch uploads successfully.

---

## Self-Review

- Spec coverage: Tasks cover recurring startup recomputation, process/network trigger queue synchronization, tray Quit/copy, 2.2 packaging identity, release docs, and full validation.
- Placeholder scan: no placeholder markers remain; code snippets and commands are concrete.
- Type consistency: plan uses existing `TaskScheduler`, `AppController`, `TaskTriggerType`, `RepeatRule`, `NetworkSample`, `TrayService`, and unittest names already present in the repo.
