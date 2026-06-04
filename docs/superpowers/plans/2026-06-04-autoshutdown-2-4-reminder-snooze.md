# AutoShutdownQt 2.4 Reminder Snooze Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add configurable pre-execution reminders and a one-click default snooze action before scheduled power actions run.

**Architecture:** Store reminder preferences in `settings_service.py`, expose them through `AppController`, check reminder thresholds from the existing scheduler tick, and show an in-app QML dialog from `Main.qml`. Keep the feature small: no native Windows notifications, no tray changes, no per-task reminder settings.

**Tech Stack:** Python 3.12, PySide6 `QObject`/`Signal`/`Property`/`Slot`, QML, `unittest`, existing `TaskScheduler` queue model.

---

## File Structure

- Modify `AutoShutdownQt/settings_service.py`: add default persisted reminder keys.
- Modify `AutoShutdownQt/controller.py`: add reminder settings, parsed reminder helpers, QML properties/signals, reminder tick checks, snooze/cancel slots, and queue task snooze support.
- Modify `AutoShutdownQt/qml/Main.qml`: add reminder settings controls and reminder dialog wired to controller slots.
- Modify `AutoShutdownQt/tests/test_practical_enhancements.py`: add controller/settings unit tests.
- Modify `AutoShutdownQt/tests/test_e5e8_ui_regressions.py`: add static QML wiring regression test.

Implementation should not create a new helper module. The behavior belongs in `AppController` because the controller already owns settings coercion, scheduler ticking, QML-facing state, and logs.

---

### Task 1: Persist Reminder Defaults

**Files:**
- Modify: `AutoShutdownQt/settings_service.py:5-24`
- Test: `AutoShutdownQt/tests/test_practical_enhancements.py`

- [ ] **Step 1: Write the failing default-settings test**

Add this method to `PracticalEnhancementsTest` near the existing settings tests:

```python
def test_default_settings_include_reminder_preferences(self):
    settings = default_settings()

    self.assertTrue(settings["reminderEnabled"])
    self.assertEqual(settings["reminderMinutesCsv"], "10,5,1")
    self.assertEqual(settings["snoozeMinutes"], 15)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_default_settings_include_reminder_preferences -v
```

Expected: FAIL with `KeyError: 'reminderEnabled'`.

- [ ] **Step 3: Add default settings**

In `AutoShutdownQt/settings_service.py`, extend `DEFAULT_SETTINGS` after the music keys and before `taskQueue`:

```python
    "reminderEnabled": True,
    "reminderMinutesCsv": "10,5,1",
    "snoozeMinutes": 15,
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_default_settings_include_reminder_preferences -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Only commit if the user has approved committing the current worktree state. Use specific paths:

```bash
git add AutoShutdownQt/settings_service.py AutoShutdownQt/tests/test_practical_enhancements.py
git commit -m "Add reminder preference defaults"
```

---

### Task 2: Add Controller Reminder Settings and Parsing

**Files:**
- Modify: `AutoShutdownQt/controller.py:18-346`
- Test: `AutoShutdownQt/tests/test_practical_enhancements.py`

- [ ] **Step 1: Write failing controller settings tests**

Add these methods to `PracticalEnhancementsTest`:

```python
def test_controller_exposes_reminder_preferences(self):
    controller = AppController()

    self.assertTrue(controller.reminderEnabled)
    self.assertEqual(controller.reminderMinutesCsv, "10,5,1")
    self.assertEqual(controller.snoozeMinutesValue, 15)

    controller.reminderEnabled = False
    controller.reminderMinutesCsv = "20, 10, 10, nope, 0, -1, 5"
    controller.snoozeMinutesValue = 30

    self.assertFalse(controller.reminderEnabled)
    self.assertEqual(controller.reminderMinutesCsv, "20, 10, 10, nope, 0, -1, 5")
    self.assertEqual(controller.snoozeMinutesValue, 30)
    self.assertEqual(controller._reminder_minutes(), [20, 10, 5])


def test_controller_reminder_parsing_falls_back_to_defaults(self):
    controller = AppController()

    controller.reminderMinutesCsv = "bad, 0, -2"
    controller.snoozeMinutesValue = 0

    self.assertEqual(controller._reminder_minutes(), [10, 5, 1])
    self.assertEqual(controller.snoozeMinutesValue, 15)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_controller_exposes_reminder_preferences AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_controller_reminder_parsing_falls_back_to_defaults -v
```

Expected: FAIL with missing `reminderEnabled`/`reminderMinutesCsv`/`snoozeMinutesValue` properties.

- [ ] **Step 3: Add signal and state**

In `AppController`, add a signal after `musicChanged = Signal()`:

```python
    reminderChanged = Signal()
```

In `__init__`, after music settings are loaded, add:

```python
        self._reminder_enabled = self._coerce_bool(settings.get("reminderEnabled"), True)
        self._reminder_minutes_csv = str(settings.get("reminderMinutesCsv") or "10,5,1")
        self._snooze_minutes_value = self._coerce_int(settings.get("snoozeMinutes"), 15, minimum=1)
        self._shown_reminders = set()
        self._reminder_dialog_title = ""
        self._reminder_dialog_body = ""
        self._reminder_dialog_snooze_text = ""
```

- [ ] **Step 4: Add QML properties**

In the properties section after `musicPlaybackMode`, add:

```python
    def getReminderEnabled(self): return self._reminder_enabled
    def setReminderEnabled(self, v):
        v = bool(v)
        if self._reminder_enabled != v:
            self._reminder_enabled = v
            self._save_settings()
            self.reminderChanged.emit()
    reminderEnabled = Property(bool, getReminderEnabled, setReminderEnabled, notify=reminderChanged)

    def getReminderMinutesCsv(self): return self._reminder_minutes_csv
    def setReminderMinutesCsv(self, v):
        v = str(v or "")
        if self._reminder_minutes_csv != v:
            self._reminder_minutes_csv = v
            self._save_settings()
            self.reminderChanged.emit()
    reminderMinutesCsv = Property(str, getReminderMinutesCsv, setReminderMinutesCsv, notify=reminderChanged)

    def getSnoozeMinutesValue(self): return self._snooze_minutes_value
    def setSnoozeMinutesValue(self, v):
        v = self._coerce_int(v, 15, minimum=1)
        if self._snooze_minutes_value != v:
            self._snooze_minutes_value = v
            self._save_settings()
            self.reminderChanged.emit()
    snoozeMinutesValue = Property(int, getSnoozeMinutesValue, setSnoozeMinutesValue, notify=reminderChanged)

    def getReminderDialogTitle(self): return self._reminder_dialog_title
    reminderDialogTitle = Property(str, getReminderDialogTitle, notify=reminderChanged)

    def getReminderDialogBody(self): return self._reminder_dialog_body
    reminderDialogBody = Property(str, getReminderDialogBody, notify=reminderChanged)

    def getReminderDialogSnoozeText(self): return self._reminder_dialog_snooze_text
    reminderDialogSnoozeText = Property(str, getReminderDialogSnoozeText, notify=reminderChanged)
```

- [ ] **Step 5: Add parsing helper**

Near the existing `_coerce_*` helpers, add:

```python
    def _reminder_minutes(self):
        values = []
        for token in self._reminder_minutes_csv.split(","):
            try:
                value = int(str(token).strip())
            except ValueError:
                continue
            if value > 0:
                values.append(value)
        unique = sorted(set(values), reverse=True)
        return unique or [10, 5, 1]
```

- [ ] **Step 6: Save new settings keys**

In `_settings_snapshot()` or the existing settings dict builder, include:

```python
            "reminderEnabled": self._reminder_enabled,
            "reminderMinutesCsv": self._reminder_minutes_csv,
            "snoozeMinutes": self._snooze_minutes_value,
```

- [ ] **Step 7: Run tests to verify they pass**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_controller_exposes_reminder_preferences AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_controller_reminder_parsing_falls_back_to_defaults -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

Only commit if the user has approved committing the current worktree state:

```bash
git add AutoShutdownQt/controller.py AutoShutdownQt/tests/test_practical_enhancements.py
git commit -m "Expose reminder settings in controller"
```

---

### Task 3: Trigger Reminder Dialog Once Per Threshold

**Files:**
- Modify: `AutoShutdownQt/controller.py:18-850`
- Test: `AutoShutdownQt/tests/test_practical_enhancements.py`

- [ ] **Step 1: Write failing reminder trigger tests**

Add these methods to `PracticalEnhancementsTest`:

```python
def test_reminder_fires_once_when_countdown_reaches_threshold(self):
    controller = AppController()
    controller.reminderMinutesCsv = "1"
    emissions = []
    controller.reminderChanged.connect(lambda: emissions.append(controller.reminderDialogTitle))
    controller._remaining_seconds = 60
    controller._status = "running"

    controller._check_execution_reminders()
    controller._check_execution_reminders()

    self.assertEqual(emissions.count("执行前提醒"), 1)
    self.assertIn("关机", controller.reminderDialogBody)
    self.assertIn("Dry-run", controller.reminderDialogBody)
    self.assertEqual(controller.reminderDialogSnoozeText, "延后 15 分钟")


def test_reminder_body_distinguishes_real_execution_mode(self):
    controller = AppController()
    controller.dryRun = False
    controller.reminderMinutesCsv = "1"
    controller._remaining_seconds = 60
    controller._status = "running"

    controller._check_execution_reminders()

    self.assertIn("真实执行", controller.reminderDialogBody)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_reminder_fires_once_when_countdown_reaches_threshold AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_reminder_body_distinguishes_real_execution_mode -v
```

Expected: FAIL with missing `_check_execution_reminders`.

- [ ] **Step 3: Add reminder check helpers**

In `controller.py`, add these methods near `_on_tick`:

```python
    def _check_execution_reminders(self):
        if not self._reminder_enabled or self._status != "running" or self._remaining_seconds <= 0:
            return
        for minute in self._reminder_minutes():
            threshold_seconds = minute * 60
            if self._remaining_seconds <= threshold_seconds and minute not in self._shown_reminders:
                self._shown_reminders.add(minute)
                self._show_execution_reminder(minute)
                return

    def _show_execution_reminder(self, minute):
        mode_text = "Dry-run：到点只记录将要执行的动作，不会真实执行。" if self._dry_run else "真实执行：到点会执行系统动作，请确认未保存工作。"
        self._reminder_dialog_title = "执行前提醒"
        self._reminder_dialog_body = f"{self.actionLabel} 将在 {self.remainingText} 后执行。\n{mode_text}"
        self._reminder_dialog_snooze_text = f"延后 {self._snooze_minutes_value} 分钟"
        self._add_log(f"执行前提醒：剩余 {minute} 分钟")
        self.reminderChanged.emit()
```

- [ ] **Step 4: Call the reminder check from `_on_tick`**

In `_on_tick`, after `self.remainingTimeChanged.emit()` and before the `if self._remaining_seconds <= 0:` block, add:

```python
        self._check_execution_reminders()
```

- [ ] **Step 5: Clear reminder tracking when cancelling and when countdown finishes**

In `cancel()`, after setting `_target_time_str`, add:

```python
        self._shown_reminders.clear()
```

In `_on_tick`, before `_execute_with_script("倒计时结束")`, add:

```python
            self._shown_reminders.clear()
```

- [ ] **Step 6: Run tests to verify they pass**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_reminder_fires_once_when_countdown_reaches_threshold AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_reminder_body_distinguishes_real_execution_mode -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

Only commit if approved:

```bash
git add AutoShutdownQt/controller.py AutoShutdownQt/tests/test_practical_enhancements.py
git commit -m "Show execution reminders before countdown actions"
```

---

### Task 4: Add Snooze Behavior for Active Countdown and Queue Tasks

**Files:**
- Modify: `AutoShutdownQt/controller.py:583-850`
- Test: `AutoShutdownQt/tests/test_practical_enhancements.py`

- [ ] **Step 1: Write failing snooze tests**

Add these methods to `PracticalEnhancementsTest`:

```python
def test_snooze_current_task_extends_active_countdown_and_resets_reminders(self):
    controller = AppController()
    controller.snoozeMinutesValue = 2
    controller._remaining_seconds = 60
    controller._status = "running"
    controller._shown_reminders.add(1)

    controller.snoozeCurrentTask()

    self.assertEqual(controller.remainingSeconds, 180)
    self.assertEqual(controller._shown_reminders, set())
    self.assertIn("已延后 2 分钟", controller.logText)


def test_snooze_current_task_extends_next_queue_task(self):
    controller = AppController()
    controller.snoozeMinutesValue = 5
    controller.startCountdown(0, 1, 0)
    task = controller._scheduler.tasks[0]
    before = task.next_run_at

    controller.snoozeCurrentTask()

    self.assertEqual(task.next_run_at, before + timedelta(minutes=5))
    self.assertIn("已延后 5 分钟", controller.logText)
```

Also add `timedelta` to the import line at the top of this test file:

```python
from datetime import timedelta
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_snooze_current_task_extends_active_countdown_and_resets_reminders AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_snooze_current_task_extends_next_queue_task -v
```

Expected: FAIL with missing `snoozeCurrentTask`.

- [ ] **Step 3: Implement `snoozeCurrentTask`**

Add this slot after existing `snoozeMinutes(self, minutes)`:

```python
    @Slot()
    def snoozeCurrentTask(self):
        minutes = self._snooze_minutes_value
        if self._status == "running" and self._timer.isActive():
            self._remaining_seconds += minutes * 60
            self._target_time_str = ""
            self._shown_reminders.clear()
            self._add_log(f"已延后 {minutes} 分钟")
            self.remainingTimeChanged.emit()
            self.targetInfoChanged.emit()
            self.reminderChanged.emit()
            return
        task = self._next_snoozable_task()
        if task is None:
            self._add_log("没有可延后的任务")
            return
        task.next_run_at = task.next_run_at + timedelta(minutes=minutes)
        if task.trigger_type == TaskTriggerType.COUNTDOWN:
            task.trigger_config["seconds"] = max(1, int(task.trigger_config.get("seconds", 0))) + minutes * 60
        self._shown_reminders.clear()
        self._save_settings()
        self._add_log(f"已延后 {minutes} 分钟")
        self.taskQueueChanged.emit()
        self.reminderChanged.emit()

    def _next_snoozable_task(self):
        candidates = [task for task in self._scheduler.tasks if task.enabled and task.next_run_at]
        if not candidates:
            return None
        return sorted(candidates, key=lambda task: (task.next_run_at, task.created_order))[0]
```

Because this code uses `timedelta`, change the existing import at the top of `controller.py` from:

```python
from datetime import datetime, timedelta
```

Keep it as-is if it already imports `timedelta`; otherwise add `timedelta`.

- [ ] **Step 4: Make existing `snoozeMinutes` reset reminder tracking**

In `snoozeMinutes(self, minutes)`, after `self._target_time_str = ""`, add:

```python
        self._shown_reminders.clear()
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_snooze_current_task_extends_active_countdown_and_resets_reminders AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_snooze_current_task_extends_next_queue_task -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

Only commit if approved:

```bash
git add AutoShutdownQt/controller.py AutoShutdownQt/tests/test_practical_enhancements.py
git commit -m "Add default snooze action for scheduled tasks"
```

---

### Task 5: Wire Reminder Settings and Dialog in QML

**Files:**
- Modify: `AutoShutdownQt/qml/Main.qml:87-98,1122-1164,1376-1438`
- Test: `AutoShutdownQt/tests/test_e5e8_ui_regressions.py`

- [ ] **Step 1: Write failing QML wiring test**

Add this method to `E5E8ButtonRegressionTest`:

```python
def test_2_4_reminder_snooze_ui_is_wired_to_controller(self):
    main = MAIN_QML.read_text(encoding="utf-8")

    for snippet in (
        "controller.reminderEnabled",
        "controller.reminderMinutesCsv",
        "controller.snoozeMinutesValue",
        "controller.reminderDialogTitle",
        "controller.reminderDialogBody",
        "controller.reminderDialogSnoozeText",
        "controller.snoozeCurrentTask()",
        "function onReminderChanged()",
        "reminderDialog.open()",
    ):
        self.assertIn(snippet, main)
    for label in ("执行前提醒", "提醒分钟", "默认延后", "取消当前任务", "知道了"):
        self.assertIn(label, main)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_e5e8_ui_regressions.E5E8ButtonRegressionTest.test_2_4_reminder_snooze_ui_is_wired_to_controller -v
```

Expected: FAIL because reminder QML snippets do not exist.

- [ ] **Step 3: Open dialog when controller changes reminder dialog title**

In `Main.qml`, inside the existing `Connections { target: controller ... }` block near `onMusicChanged`, add:

```qml
        function onReminderChanged() {
            if (controller.reminderDialogTitle !== "") {
                reminderDialog.open()
            }
        }
```

- [ ] **Step 4: Add settings controls**

In the settings page `ColumnLayout`, after the music autoplay row and before the warning `Text`, add:

```qml
                    RowLayout {
                        Layout.fillWidth: true
                        Text { Layout.fillWidth: true; text: "执行前提醒"; color: Theme.textPrimary; font.pixelSize: 16; font.weight: Font.Bold }
                        FluentSwitch { checked: controller.reminderEnabled; onCheckedChanged: controller.reminderEnabled = checked }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        Text { Layout.preferredWidth: 90; text: "提醒分钟"; color: Theme.textSecondary; font.pixelSize: 13 }
                        TextField {
                            Layout.fillWidth: true
                            text: controller.reminderMinutesCsv
                            placeholderText: "10,5,1"
                            onEditingFinished: controller.reminderMinutesCsv = text
                        }
                        Text { Layout.preferredWidth: 210; text: "逗号分隔，例如 10,5,1"; color: Theme.textSecondary; font.pixelSize: 12 }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        Text { Layout.preferredWidth: 90; text: "默认延后"; color: Theme.textSecondary; font.pixelSize: 13 }
                        TextField {
                            Layout.preferredWidth: 96
                            text: String(controller.snoozeMinutesValue)
                            inputMethodHints: Qt.ImhDigitsOnly
                            onEditingFinished: controller.snoozeMinutesValue = mainWindow.safeInt(text, 15)
                        }
                        Text { Layout.fillWidth: true; text: "分钟，提醒弹窗按钮会使用这个时长"; color: Theme.textSecondary; font.pixelSize: 12 }
                    }
```

- [ ] **Step 5: Add reminder dialog**

Add this `Dialog` near the existing `liveModeConfirmDialog`:

```qml
    Dialog {
        id: reminderDialog
        modal: true
        title: controller.reminderDialogTitle
        standardButtons: Dialog.NoButton
        anchors.centerIn: parent
        width: 440

        background: Rectangle {
            radius: Theme.radiusLg
            color: Theme.cardGlassActive
            border.color: controller.dryRun ? Theme.success : Theme.danger
            border.width: 1
        }

        contentItem: ColumnLayout {
            spacing: 14
            Text {
                Layout.fillWidth: true
                text: controller.reminderDialogBody
                color: Theme.textPrimary
                font.pixelSize: 14
                wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                NeonButton {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 38
                    compact: true
                    text: controller.reminderDialogSnoozeText
                    onClicked: {
                        controller.snoozeCurrentTask()
                        reminderDialog.close()
                    }
                }
                NeonButton {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 38
                    compact: true
                    variant: "danger"
                    text: "取消当前任务"
                    onClicked: {
                        controller.cancel()
                        reminderDialog.close()
                    }
                }
                NeonButton {
                    Layout.preferredWidth: 92
                    Layout.preferredHeight: 38
                    compact: true
                    variant: "secondary"
                    text: "知道了"
                    onClicked: reminderDialog.close()
                }
            }
        }
    }
```

- [ ] **Step 6: Run QML wiring test**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_e5e8_ui_regressions.E5E8ButtonRegressionTest.test_2_4_reminder_snooze_ui_is_wired_to_controller -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

Only commit if approved:

```bash
git add AutoShutdownQt/qml/Main.qml AutoShutdownQt/tests/test_e5e8_ui_regressions.py
git commit -m "Wire reminder snooze dialog in QML"
```

---

### Task 6: Run Focused and Full Regression Tests

**Files:**
- Verify: `AutoShutdownQt/tests/test_practical_enhancements.py`
- Verify: `AutoShutdownQt/tests/test_e5e8_ui_regressions.py`
- Verify: all `AutoShutdownQt/tests`

- [ ] **Step 1: Run focused practical tests**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements -v
```

Expected: PASS.

- [ ] **Step 2: Run focused QML static tests**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_e5e8_ui_regressions -v
```

Expected: PASS.

- [ ] **Step 3: Run full suite**

Run:

```bash
python -m unittest discover AutoShutdownQt/tests -v
```

Expected: all tests PASS.

- [ ] **Step 4: Fix only failures caused by this feature**

If a test fails because of the reminder feature, apply the smallest fix in the file that introduced the failure. Do not refactor unrelated controller, QML, or scheduler code.

- [ ] **Step 5: Commit final fixes**

Only commit if approved and only if there are fixes beyond prior tasks:

```bash
git add AutoShutdownQt/controller.py AutoShutdownQt/qml/Main.qml AutoShutdownQt/settings_service.py AutoShutdownQt/tests/test_practical_enhancements.py AutoShutdownQt/tests/test_e5e8_ui_regressions.py
git commit -m "Stabilize reminder snooze regressions"
```

---

## Self-Review

- Spec coverage: reminder defaults, configurable CSV, configurable snooze duration, in-app dialog, dry-run/live copy, once-per-threshold behavior, snooze, cancel, persistence, QML controls, and tests are covered by Tasks 1-6.
- Scope check: no native Windows notifications, tray changes, multiple snooze buttons, or per-task settings are included.
- Type consistency: controller property names are `reminderEnabled`, `reminderMinutesCsv`, `snoozeMinutesValue`, `reminderDialogTitle`, `reminderDialogBody`, and `reminderDialogSnoozeText`; QML and tests use the same names.
- Placeholder scan: no TBD/TODO/fill-later instructions are present.
