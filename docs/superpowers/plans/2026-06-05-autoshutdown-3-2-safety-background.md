# 定时关机助手 3.2 Safety Background Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the 3.2 safety/background UX release: first-run safety guide, one-time tray-close hint, stronger live-mode warnings, clearer task source labels, and 3.2 release docs/packaging updates.

**Architecture:** Keep the existing controller/QML structure. Add two persisted acknowledgement settings exposed through controller properties/slots, keep the hint dialogs in `Main.qml`, centralize source-label text in controller helpers, and update packaging/docs after behavior tests pass.

**Tech Stack:** Python 3.12, PySide6/QML, `unittest`, PyInstaller, Inno Setup.

---

## File Structure

- Modify `AutoShutdownQt/settings_service.py`: add 3.2 default acknowledgement settings.
- Modify `AutoShutdownQt/controller.py`: expose acknowledgement properties/slots and task-source label helper.
- Modify `AutoShutdownQt/qml/Main.qml`: add first-run guide, close-to-tray hint, live-mode warning copy, and 3.2 version text.
- Modify `AutoShutdownQt/qml/components/ConfirmDialog.qml`: strengthen immediate execution confirmation copy.
- Modify `AutoShutdownQt/tests/test_practical_enhancements.py`: controller/settings behavior tests.
- Modify `AutoShutdownQt/tests/test_e5e8_ui_regressions.py`: QML/static UI regression tests and 3.2 version assertions.
- Modify `AutoShutdownQt/tests/test_release_packaging.py`: 3.2 artifact expectations.
- Modify `AutoShutdownQt/main.py`: application version bump.
- Modify `AutoShutdownQt/package_release.py`: release version bump and checklist additions.
- Create `AutoShutdownQt/AutoShutdownQt-3.2.spec`: copied from 3.1 with 3.2 bundle name.
- Create `AutoShutdownQt/AutoShutdownQt-3.2.iss`: copied from 3.1 with 3.2 names.
- Modify `.gitignore`: unignore 3.2 spec/iss.
- Modify `README.md`: current release and safety/background docs.
- Create `RELEASE_NOTES_v3.2.md`: 3.2 release notes.

## Task 1: Add persisted 3.2 acknowledgement settings

**Files:**
- Modify: `AutoShutdownQt/settings_service.py:5-36`
- Test: `AutoShutdownQt/tests/test_practical_enhancements.py`

- [ ] **Step 1: Write failing settings test**

Add this test after `test_default_settings_include_idle_trigger_preferences` in `AutoShutdownQt/tests/test_practical_enhancements.py`:

```python
    def test_default_settings_include_3_2_safety_acknowledgements(self):
        settings = default_settings()

        self.assertFalse(settings["firstRunSafetyGuideShown"])
        self.assertFalse(settings["trayCloseHintShown"])
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_default_settings_include_3_2_safety_acknowledgements -v
```

Expected: FAIL with `KeyError: 'firstRunSafetyGuideShown'`.

- [ ] **Step 3: Add default settings**

In `AutoShutdownQt/settings_service.py`, add the two keys at the end of `DEFAULT_SETTINGS`:

```python
    "startMinimizedToTray": False,
    "firstRunSafetyGuideShown": False,
    "trayCloseHintShown": False,
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_default_settings_include_3_2_safety_acknowledgements -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add AutoShutdownQt/settings_service.py AutoShutdownQt/tests/test_practical_enhancements.py
git commit -m "Add 3.2 safety acknowledgement settings"
```

## Task 2: Expose safety acknowledgement state in controller

**Files:**
- Modify: `AutoShutdownQt/controller.py`
- Test: `AutoShutdownQt/tests/test_practical_enhancements.py`

- [ ] **Step 1: Write failing controller test**

Add this test after the default acknowledgement settings test:

```python
    def test_controller_persists_3_2_safety_acknowledgements(self):
        controller = AppController()

        self.assertFalse(controller.firstRunSafetyGuideShown)
        self.assertFalse(controller.trayCloseHintShown)

        controller.acknowledgeFirstRunSafetyGuide()
        controller.acknowledgeTrayCloseHint()

        self.assertTrue(controller.firstRunSafetyGuideShown)
        self.assertTrue(controller.trayCloseHintShown)
        saved = controller._settings_payload()
        self.assertTrue(saved["firstRunSafetyGuideShown"])
        self.assertTrue(saved["trayCloseHintShown"])
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_controller_persists_3_2_safety_acknowledgements -v
```

Expected: FAIL with missing property or slot.

- [ ] **Step 3: Add controller state**

In `AppController.__init__`, after `self._start_minimized_to_tray = ...`, add:

```python
        self._first_run_safety_guide_shown = self._coerce_bool(settings.get("firstRunSafetyGuideShown"), False)
        self._tray_close_hint_shown = self._coerce_bool(settings.get("trayCloseHintShown"), False)
```

- [ ] **Step 4: Add properties and slots**

In `AutoShutdownQt/controller.py`, near the existing startup properties, add:

```python
    def getFirstRunSafetyGuideShown(self):
        return self._first_run_safety_guide_shown

    @Slot()
    def acknowledgeFirstRunSafetyGuide(self):
        if not self._first_run_safety_guide_shown:
            self._first_run_safety_guide_shown = True
            self._save_settings()
            self.startupChanged.emit()

    firstRunSafetyGuideShown = Property(bool, getFirstRunSafetyGuideShown, notify=startupChanged)

    def getTrayCloseHintShown(self):
        return self._tray_close_hint_shown

    @Slot()
    def acknowledgeTrayCloseHint(self):
        if not self._tray_close_hint_shown:
            self._tray_close_hint_shown = True
            self._save_settings()
            self.startupChanged.emit()

    trayCloseHintShown = Property(bool, getTrayCloseHintShown, notify=startupChanged)
```

- [ ] **Step 5: Persist in settings payload**

In `_settings_payload()`, add:

```python
            "firstRunSafetyGuideShown": self._first_run_safety_guide_shown,
            "trayCloseHintShown": self._tray_close_hint_shown,
```

- [ ] **Step 6: Run test to verify it passes**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_controller_persists_3_2_safety_acknowledgements -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add AutoShutdownQt/controller.py AutoShutdownQt/tests/test_practical_enhancements.py
git commit -m "Expose 3.2 safety acknowledgement state"
```

## Task 3: Add first-run safety guide UI

**Files:**
- Modify: `AutoShutdownQt/qml/Main.qml`
- Test: `AutoShutdownQt/tests/test_e5e8_ui_regressions.py`

- [ ] **Step 1: Write failing QML regression test**

Add this test after `test_2_5_background_experience_ui_is_wired_to_controller`:

```python
    def test_3_2_first_run_safety_guide_is_wired(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertIn("id: firstRunSafetyGuideDialog", main)
        self.assertIn("controller.firstRunSafetyGuideShown", main)
        self.assertIn("controller.acknowledgeFirstRunSafetyGuide()", main)
        self.assertIn("Dry-run 默认开启", main)
        self.assertIn("关闭 Dry-run 后可能真实执行", main)
        self.assertIn("右下角托盘", main)
        self.assertIn("彻底退出", main)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_e5e8_ui_regressions.E5E8ButtonRegressionTest.test_3_2_first_run_safety_guide_is_wired -v
```

Expected: FAIL because the dialog is absent.

- [ ] **Step 3: Open guide on startup**

In `AutoShutdownQt/qml/Main.qml`, add this to the top-level `Window` near `Connections`:

```qml
    Component.onCompleted: {
        if (!controller.firstRunSafetyGuideShown) {
            firstRunSafetyGuideDialog.open()
        }
    }
```

- [ ] **Step 4: Add dialog near existing dialogs**

Before `ConfirmDialog { id: confirmDialog ... }`, add:

```qml
    Dialog {
        id: firstRunSafetyGuideDialog
        modal: true
        standardButtons: Dialog.NoButton
        width: 500
        padding: 22
        anchors.centerIn: parent

        background: Rectangle {
            color: Theme.cardGlassActive
            radius: Theme.radiusLg
            border.color: Theme.warning
            border.width: 1
        }

        contentItem: ColumnLayout {
            spacing: Theme.spaceMd
            Text { Layout.fillWidth: true; text: "首次启动安全说明"; color: Theme.textPrimary; font.pixelSize: 20; font.weight: Font.Bold }
            Text { Layout.fillWidth: true; text: "Dry-run 默认开启：应用只记录将要执行的动作，不会真实关机、重启、睡眠、休眠、注销、锁定或运行脚本。"; color: Theme.textSecondary; font.pixelSize: 14; wrapMode: Text.WordWrap }
            Text { Layout.fillWidth: true; text: "关闭 Dry-run 后可能真实执行 Windows 电源动作，请先确认任务、触发器、脚本路径和未保存工作。"; color: Theme.danger; font.pixelSize: 14; wrapMode: Text.WordWrap }
            Text { Layout.fillWidth: true; text: "右下角托盘可用时，关闭窗口会隐藏到后台，倒计时、队列和触发器仍会继续。"; color: Theme.textSecondary; font.pixelSize: 14; wrapMode: Text.WordWrap }
            Text { Layout.fillWidth: true; text: "如需彻底退出，请右键右下角托盘图标并选择 Quit。"; color: Theme.textSecondary; font.pixelSize: 14; wrapMode: Text.WordWrap }
        }

        footer: Item {
            implicitHeight: 64
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 22
                anchors.rightMargin: 22
                anchors.bottomMargin: 16
                Item { Layout.fillWidth: true }
                NeonButton {
                    compact: true
                    variant: "primary"
                    text: "我知道了"
                    onClicked: {
                        controller.acknowledgeFirstRunSafetyGuide()
                        firstRunSafetyGuideDialog.close()
                    }
                }
            }
        }
    }
```

- [ ] **Step 5: Run QML test**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_e5e8_ui_regressions.E5E8ButtonRegressionTest.test_3_2_first_run_safety_guide_is_wired -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add AutoShutdownQt/qml/Main.qml AutoShutdownQt/tests/test_e5e8_ui_regressions.py
git commit -m "Add first-run safety guide"
```

## Task 4: Add one-time close-to-tray hint

**Files:**
- Modify: `AutoShutdownQt/qml/Main.qml`
- Test: `AutoShutdownQt/tests/test_e5e8_ui_regressions.py`

- [ ] **Step 1: Write failing QML regression test**

Add this test after the first-run guide test:

```python
    def test_3_2_close_to_tray_hint_is_wired(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertIn("id: trayCloseHintDialog", main)
        self.assertIn("controller.trayCloseHintShown", main)
        self.assertIn("controller.acknowledgeTrayCloseHint()", main)
        self.assertIn("trayCloseHintDialog.open()", main)
        self.assertIn("任务、倒计时和触发器仍会继续", main)
        self.assertIn("controller.minimizeToTray()", main)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_e5e8_ui_regressions.E5E8ButtonRegressionTest.test_3_2_close_to_tray_hint_is_wired -v
```

Expected: FAIL because the tray close hint dialog is absent.

- [ ] **Step 3: Update close handler**

Replace the existing top-level `onClosing` block in `Main.qml` with:

```qml
    onClosing: function(close) {
        if (controller.trayAvailable && !trayCloseRequested) {
            close.accepted = false
            if (!controller.trayCloseHintShown) {
                trayCloseHintDialog.open()
            } else {
                controller.minimizeToTray()
            }
        }
    }
```

- [ ] **Step 4: Add tray hint dialog**

Before `ConfirmDialog { id: confirmDialog ... }`, add:

```qml
    Dialog {
        id: trayCloseHintDialog
        modal: true
        standardButtons: Dialog.NoButton
        width: 480
        padding: 22
        anchors.centerIn: parent

        background: Rectangle {
            color: Theme.cardGlassActive
            radius: Theme.radiusLg
            border.color: Theme.primary
            border.width: 1
        }

        contentItem: ColumnLayout {
            spacing: Theme.spaceMd
            Text { Layout.fillWidth: true; text: "将隐藏到右下角托盘"; color: Theme.textPrimary; font.pixelSize: 20; font.weight: Font.Bold }
            Text { Layout.fillWidth: true; text: "任务、倒计时和触发器仍会继续运行。"; color: Theme.textSecondary; font.pixelSize: 14; wrapMode: Text.WordWrap }
            Text { Layout.fillWidth: true; text: "要彻底退出，请右键右下角托盘图标选择 Quit。"; color: Theme.textSecondary; font.pixelSize: 14; wrapMode: Text.WordWrap }
        }

        footer: Item {
            implicitHeight: 64
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 22
                anchors.rightMargin: 22
                anchors.bottomMargin: 16
                Item { Layout.fillWidth: true }
                NeonButton {
                    compact: true
                    variant: "primary"
                    text: "隐藏到托盘"
                    onClicked: {
                        controller.acknowledgeTrayCloseHint()
                        trayCloseHintDialog.close()
                        controller.minimizeToTray()
                    }
                }
            }
        }
    }
```

- [ ] **Step 5: Run QML test**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_e5e8_ui_regressions.E5E8ButtonRegressionTest.test_3_2_close_to_tray_hint_is_wired -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add AutoShutdownQt/qml/Main.qml AutoShutdownQt/tests/test_e5e8_ui_regressions.py
git commit -m "Add one-time tray close hint"
```

## Task 5: Strengthen live-mode warnings

**Files:**
- Modify: `AutoShutdownQt/qml/Main.qml`
- Modify: `AutoShutdownQt/qml/components/ConfirmDialog.qml`
- Test: `AutoShutdownQt/tests/test_e5e8_ui_regressions.py`

- [ ] **Step 1: Write failing QML regression test**

Add this test after the tray hint test:

```python
    def test_3_2_live_mode_warning_copy_is_stronger(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        dialog = CONFIRM_DIALOG_QML.read_text(encoding="utf-8")

        self.assertIn("真实执行模式：请确认未保存工作", main)
        self.assertIn("LIVE MODE 会真实执行当前动作", dialog)
        self.assertIn("可能导致关机、重启、睡眠、休眠、注销或锁定", dialog)
        self.assertIn("controller.dryRun ?", dialog)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_e5e8_ui_regressions.E5E8ButtonRegressionTest.test_3_2_live_mode_warning_copy_is_stronger -v
```

Expected: FAIL because the stronger copy is absent.

- [ ] **Step 3: Add live warning near immediate execution controls**

In `Main.qml`, near each `立即执行当前动作` button section, add a visible-on-live-mode text line close to the button. Example inside the surrounding `ColumnLayout`:

```qml
                            Text {
                                Layout.fillWidth: true
                                visible: !controller.dryRun
                                text: "真实执行模式：请确认未保存工作，当前动作可能立即影响系统电源状态。"
                                color: Theme.danger
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                            }
```

If there are two immediate execution sections, add the same warning to both sections.

- [ ] **Step 4: Update confirm dialog copy**

In `AutoShutdownQt/qml/components/ConfirmDialog.qml`, update the body text expression to include mode-aware wording:

```qml
        Text {
            Layout.fillWidth: true
            text: controller.dryRun
                ? "Dry-run 将只记录当前动作，不会真实执行系统电源操作。"
                : "LIVE MODE 会真实执行当前动作，可能导致关机、重启、睡眠、休眠、注销或锁定。请确认未保存工作。"
            color: controller.dryRun ? Theme.textSecondary : Theme.danger
            font.pixelSize: 13
            wrapMode: Text.WordWrap
        }
```

Keep the existing action label/title and accept/reject button behavior unchanged.

- [ ] **Step 5: Run QML test**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_e5e8_ui_regressions.E5E8ButtonRegressionTest.test_3_2_live_mode_warning_copy_is_stronger -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add AutoShutdownQt/qml/Main.qml AutoShutdownQt/qml/components/ConfirmDialog.qml AutoShutdownQt/tests/test_e5e8_ui_regressions.py
git commit -m "Strengthen live mode warning copy"
```

## Task 6: Centralize task source labels

**Files:**
- Modify: `AutoShutdownQt/controller.py`
- Test: `AutoShutdownQt/tests/test_practical_enhancements.py`

- [ ] **Step 1: Write failing source-label test**

Add this test near the history/reminder tests:

```python
    def test_controller_formats_task_source_labels(self):
        controller = AppController()

        self.assertEqual(controller.taskSourceLabel("countdown"), "手动倒计时")
        self.assertEqual(controller.taskSourceLabel("clock"), "指定时间")
        self.assertEqual(controller.taskSourceLabel("template"), "模板任务")
        self.assertEqual(controller.taskSourceLabel("process"), "进程退出触发")
        self.assertEqual(controller.taskSourceLabel("network"), "网络闲置触发")
        self.assertEqual(controller.taskSourceLabel("idle"), "空闲触发")
        self.assertEqual(controller.taskSourceLabel("queue"), "队列任务")
        self.assertEqual(controller.taskSourceLabel("reminder"), "执行前提醒")
        self.assertEqual(controller.taskSourceLabel("unknown"), "unknown")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_controller_formats_task_source_labels -v
```

Expected: FAIL because `taskSourceLabel` does not exist.

- [ ] **Step 3: Add source label map and slot**

In `AutoShutdownQt/controller.py`, add a module-level constant near the imports:

```python
TASK_SOURCE_LABELS = {
    "countdown": "手动倒计时",
    "clock": "指定时间",
    "template": "模板任务",
    "process": "进程退出触发",
    "network": "网络闲置触发",
    "idle": "空闲触发",
    "queue": "队列任务",
    "reminder": "执行前提醒",
}
```

Inside `AppController`, add:

```python
    @Slot(str, result=str)
    def taskSourceLabel(self, source):
        return TASK_SOURCE_LABELS.get(str(source), str(source))
```

- [ ] **Step 4: Use labels in history recording**

Update `_record_history()` so the message includes a label prefix for new entries unless the message already starts with that label:

```python
    def _record_history(self, event, action, source, task_id, message):
        self._history_settings["taskHistoryLimit"] = self._history_limit
        source_label = self.taskSourceLabel(source)
        display_message = message if message.startswith(source_label) else f"{source_label}：{message}"
        append_history_event(
            self._history_settings,
            HistoryEvent(
                event=event,
                action=action,
                source=source,
                mode="dry-run" if self._dry_run else "live",
                task_id=task_id,
                message=display_message,
            ),
            limit=self._history_limit,
        )
        self._save_settings()
        self.historyChanged.emit()
```

- [ ] **Step 5: Run source-label test**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_controller_formats_task_source_labels -v
```

Expected: PASS.

- [ ] **Step 6: Run affected history tests**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_controller_records_create_snooze_cancel_and_dry_run_history AutoShutdownQt.tests.test_practical_enhancements.PracticalEnhancementsTest.test_controller_records_history_and_notifies_for_reminder -v
```

Expected: PASS. Existing substring assertions should still pass because the original message text is preserved after the prefix.

- [ ] **Step 7: Commit**

```bash
git add AutoShutdownQt/controller.py AutoShutdownQt/tests/test_practical_enhancements.py
git commit -m "Centralize task source labels"
```

## Task 7: Bump app and release packaging to 3.2

**Files:**
- Modify: `AutoShutdownQt/main.py`
- Modify: `AutoShutdownQt/package_release.py`
- Create: `AutoShutdownQt/AutoShutdownQt-3.2.spec`
- Create: `AutoShutdownQt/AutoShutdownQt-3.2.iss`
- Modify: `.gitignore`
- Test: `AutoShutdownQt/tests/test_release_packaging.py`
- Test: `AutoShutdownQt/tests/test_e5e8_ui_regressions.py`

- [ ] **Step 1: Copy release config files**

Create `AutoShutdownQt/AutoShutdownQt-3.2.spec` by copying `AutoShutdownQt/AutoShutdownQt-3.1.spec`, then change only:

```python
    name="定时关机助手-3.2",
```

Create `AutoShutdownQt/AutoShutdownQt-3.2.iss` by copying `AutoShutdownQt/AutoShutdownQt-3.1.iss`, then replace every `3.1` release-name occurrence with `3.2`.

- [ ] **Step 2: Update `.gitignore` whitelist**

Add these lines after the 3.1 whitelist entries:

```gitignore
!AutoShutdownQt/AutoShutdownQt-3.2.spec
!AutoShutdownQt/AutoShutdownQt-3.2.iss
```

- [ ] **Step 3: Write failing version tests**

In `AutoShutdownQt/tests/test_e5e8_ui_regressions.py`, update version assertions from `v3.1` to `v3.2` and `app.setApplicationVersion("3.1")` to `app.setApplicationVersion("3.2")`.

In `AutoShutdownQt/tests/test_release_packaging.py`, update expected artifact names from `3.1` to `3.2`.

- [ ] **Step 4: Run tests to verify they fail**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_e5e8_ui_regressions AutoShutdownQt.tests.test_release_packaging -v
```

Expected: FAIL with stale `3.1` app/package strings.

- [ ] **Step 5: Bump application version**

In `AutoShutdownQt/main.py`, change:

```python
app.setApplicationVersion("3.2")
```

In `AutoShutdownQt/qml/Main.qml`, update visible version strings:

```qml
text: "v3.2 · 右侧状态栏"
```

and any `定时关机助手 v3.1` text to `定时关机助手 v3.2`.

- [ ] **Step 6: Bump package release script**

In `AutoShutdownQt/package_release.py`, change:

```python
VERSION = "3.2"
```

Add checklist lines inside `create_release_checklist()` near the existing safety/tray checks:

```python
        "- [ ] Verify first-run safety guide appears once on a fresh config.\n"
        "- [ ] Verify first close-to-tray action shows the tray background hint once.\n"
        "- [ ] Verify LIVE MODE warning copy is visible before immediate execution.\n"
```

- [ ] **Step 7: Run release/version tests**

Run:

```bash
python -m unittest AutoShutdownQt.tests.test_e5e8_ui_regressions AutoShutdownQt.tests.test_release_packaging -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add .gitignore AutoShutdownQt/main.py AutoShutdownQt/package_release.py AutoShutdownQt/qml/Main.qml AutoShutdownQt/AutoShutdownQt-3.2.spec AutoShutdownQt/AutoShutdownQt-3.2.iss AutoShutdownQt/tests/test_e5e8_ui_regressions.py AutoShutdownQt/tests/test_release_packaging.py
git commit -m "Prepare 3.2 release packaging"
```

## Task 8: Update README and 3.2 release notes

**Files:**
- Modify: `README.md`
- Create: `RELEASE_NOTES_v3.2.md`

- [ ] **Step 1: Update README current release**

In `README.md`, update:

- Title: `# 定时关机助手 3.2`
- Current release text: `当前版本是 **定时关机助手 3.2**`
- Artifact names:
  - `定时关机助手-3.2-Setup.exe`
  - `定时关机助手-3.2.zip`
  - `dist/定时关机助手-3.2/`
  - `dist/release-checklist-v3.2.md`
- GitHub release tag: `v3.2`

Add this bullet in 功能特性 near safety/tray bullets:

```markdown
- **首次启动安全说明**：首次运行会说明 Dry-run、真实执行风险、托盘后台运行和彻底退出方式。
- **关闭到托盘提示**：首次关闭窗口到托盘前会提示任务和触发器仍会继续运行。
```

- [ ] **Step 2: Create release notes**

Create `RELEASE_NOTES_v3.2.md`:

```markdown
# 定时关机助手 3.2 Release Notes

定时关机助手 3.2 是安全与后台体验增强版本，重点减少误操作并让后台运行状态更清楚。

## Highlights

- 新增首次启动安全说明：解释 Dry-run 默认开启、真实执行风险、托盘后台运行和彻底退出方式。
- 新增关闭到托盘提示：首次关闭窗口时说明任务、倒计时和触发器仍会继续运行。
- 强化 LIVE MODE 提示：真实执行模式下，立即执行前的风险文案更醒目。
- 优化任务来源表达：队列、提醒和新历史记录更清楚标记手动倒计时、指定时间、模板、进程、网络和空闲触发来源。
- 继续保留 3.1 的安装器、便携 zip、空闲自动关机、任务历史、Windows 通知和托盘后台体验。

## Safety

- Dry-run 默认开启，不会真实执行关机、重启、注销、锁定、睡眠、休眠或外部脚本。
- 关闭 Dry-run 后，倒计时、固定时间、进程退出、网络闲置和空闲自动关机都可能执行真实 Windows 电源动作。
- 当前 exe/安装器未做代码签名，Windows 首次运行时可能出现安全提示。

## Artifacts

- `dist/定时关机助手-3.2-Setup.exe`
- `dist/定时关机助手-3.2.zip`
- `dist/SHA256SUMS.txt`
- `dist/release-checklist-v3.2.md`
```

- [ ] **Step 3: Commit**

```bash
git add README.md RELEASE_NOTES_v3.2.md
git commit -m "Document 3.2 safety release"
```

## Task 9: Final verification

**Files:**
- All changed files

- [ ] **Step 1: Run full unit/static test suite**

Run:

```bash
python -m unittest discover AutoShutdownQt/tests -v
```

Expected: PASS.

- [ ] **Step 2: Check working tree**

Run:

```bash
git status --short
```

Expected: only intentional files changed/untracked if commits were skipped by operator policy. If commits were made, working tree should be clean except unrelated pre-existing files.

- [ ] **Step 3: Build release artifacts only when ready**

Run only on a release machine with PyInstaller and Inno Setup installed:

```bash
python AutoShutdownQt/package_release.py
```

Expected artifacts:

```text
dist/定时关机助手-3.2/
dist/定时关机助手-3.2.zip
dist/定时关机助手-3.2-Setup.exe
dist/SHA256SUMS.txt
dist/release-checklist-v3.2.md
```

- [ ] **Step 4: Manual safety validation**

Use a fresh settings file and keep Dry-run enabled:

```text
1. Launch the app and verify the first-run safety guide appears.
2. Click 我知道了, restart, and verify the guide does not reappear.
3. Click the close button with tray available and verify the tray hint appears.
4. Confirm the tray hint and verify the app hides to tray.
5. Restore app, close again, and verify it hides without repeating the hint.
6. Turn Dry-run off and verify LIVE MODE warning copy is visible before immediate execution.
7. Do not execute real shutdown, restart, sleep, hibernate, logoff, lock, or scripts during validation.
```

## Self-review

- Spec coverage: first-run guide is Task 3; close-to-tray hint is Task 4; live-mode warnings are Task 5; task source labels are Task 6; docs/release are Tasks 7-8; verification is Task 9.
- Placeholder scan: no TBD/TODO/fill-in placeholders remain.
- Type consistency: settings keys are `firstRunSafetyGuideShown` and `trayCloseHintShown`; controller slots are `acknowledgeFirstRunSafetyGuide()` and `acknowledgeTrayCloseHint()`; QML references match the controller names.
