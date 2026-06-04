# AutoShutdownQt 2.3 Command Center UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert AutoShutdownQt 2.3 into a clearer single-page command center UI while preserving 2.2 scheduling behavior and safety guarantees.

**Architecture:** Keep the existing Python/controller/scheduler boundaries and prefer QML-only layout changes. Add controller summary properties only if static QML cannot express the command cards cleanly. Package identity and docs move from 2.2 to 2.3 after UI tests pass.

**Tech Stack:** Python 3.12, PySide6/QML, unittest, PyInstaller packaging script.

---

## File Structure

- Modify: `AutoShutdownQt/qml/Main.qml` — single-page command center layout, safety strip, command cards, queue dashboard, recent activity copy.
- Modify: `AutoShutdownQt/tests/test_e5e8_ui_regressions.py` — static QML regression coverage for 2.3 command center text and layout markers.
- Modify: `AutoShutdownQt/main.py` — application version string moves to `2.3`.
- Modify: `AutoShutdownQt/package_release.py` — release identity, checklist, manifest archive names move to `2.3`.
- Create: `AutoShutdownQt/AutoShutdownQt-2.3.spec` — versioned PyInstaller spec matching 2.3 package identity.
- Modify: `AutoShutdownQt/tests/test_release_packaging.py` — package/release tests move to 2.3 identity and checklist expectations.
- Modify: `.gitignore` — allow committing `AutoShutdownQt/AutoShutdownQt-2.3.spec`.
- Modify: `README.md` — current release and packaging docs move to 2.3.
- Create: `RELEASE_NOTES_v2.3.md` — document UI polish release and safety notes.

---

### Task 1: Protect command center QML with failing static tests

**Files:**
- Modify: `AutoShutdownQt/tests/test_e5e8_ui_regressions.py`
- Test: `AutoShutdownQt/tests/test_e5e8_ui_regressions.py`

- [ ] **Step 1: Add command center regression test**

Add this method inside `E5E8ButtonRegressionTest`:

```python
    def test_2_3_command_center_copy_and_cards_are_present(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        for snippet in (
            'title: "AutoShutdown v2.3"',
            'AutoShutdown v2.3',
            'v2.3 · Command Center',
            'Command Center',
            '安全状态',
            'Dry-run safety',
            'Current action',
            'Tray / background',
            'Queue count',
            'Next task',
            'Active triggers',
            'Queue health',
            'Quick create',
            'Task Queue Dashboard',
            'Recent activity',
        ):
            self.assertIn(snippet, main)
```

- [ ] **Step 2: Add single-page structure regression test**

Add this method inside `E5E8ButtonRegressionTest`:

```python
    def test_2_3_uses_single_page_command_center_without_sidebar_navigation(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertIn("ScrollView {", main)
        self.assertIn("id: commandCenterScroll", main)
        self.assertIn("id: safetyStrip", main)
        self.assertIn("id: commandCardsRow", main)
        self.assertIn("id: taskQueueDashboard", main)
        self.assertNotIn('readonly property var pages: ["总览", "定时", "任务", "智能触发", "脚本", "设置"]', main)
        self.assertNotIn("id: sidebar", main)
```

- [ ] **Step 3: Run failing UI tests**

Run: `python -m unittest AutoShutdownQt.tests.test_e5e8_ui_regressions -v`

Expected: FAIL because 2.3 command center strings and single-page markers are not present.

---

### Task 2: Restructure `Main.qml` into a single command center

**Files:**
- Modify: `AutoShutdownQt/qml/Main.qml`
- Test: `AutoShutdownQt/tests/test_e5e8_ui_regressions.py`

- [ ] **Step 1: Update title/version strings**

Change the window title and subtitle strings:

```qml
title: "AutoShutdown v2.3"
```

```qml
text: "v2.3 · Command Center"
```

- [ ] **Step 2: Remove sidebar page navigation state**

Remove these page-navigation properties from `Main.qml`:

```qml
property int currentPage: 0
readonly property int sidebarWidth: 224
readonly property var pages: ["总览", "定时", "任务", "智能触发", "脚本", "设置"]
```

Keep `topBarHeight`, `outerMargin`, `queueRowModel`, `dryRunSwitchSyncing`, and `trayCloseRequested`.

- [ ] **Step 3: Replace content host with one scroll view**

Replace the sidebar and multi-page `contentHost` block with one `ScrollView` named `commandCenterScroll`:

```qml
    ScrollView {
        id: commandCenterScroll
        x: outerMargin
        y: topBarHeight + outerMargin
        width: parent.width - outerMargin * 2
        height: parent.height - y - outerMargin
        clip: true
        contentWidth: availableWidth

        ColumnLayout {
            width: commandCenterScroll.availableWidth
            spacing: 16

            Text {
                text: "Command Center"
                color: Theme.textPrimary
                font.pixelSize: 28
                font.weight: Font.Bold
            }

            NeonCard {
                id: safetyStrip
                Layout.fillWidth: true
                Layout.preferredHeight: 86
                cardColor: Theme.cardGlassActive
                cardBorderColor: controller.dryRun ? Theme.success : Theme.danger
                active: true
                activeBorderColor: controller.dryRun ? Theme.success : Theme.danger

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12

                    StatusMiniCard { label: "安全状态"; value: controller.dryRun ? "Dry-run safety" : "LIVE MODE"; accentColor: controller.dryRun ? Theme.success : Theme.danger }
                    StatusMiniCard { label: "Current action"; value: controller.actionLabel; accentColor: Theme.primary }
                    StatusMiniCard { label: "Tray / background"; value: "Close-to-tray when available"; accentColor: Theme.e5Blue }
                    StatusMiniCard { label: "Queue count"; value: String(mainWindow.queueRowModel.length); accentColor: Theme.warning }
                }
            }

            RowLayout {
                id: commandCardsRow
                Layout.fillWidth: true
                Layout.preferredHeight: 136
                spacing: 14

                CommandSummaryCard { titleText: "Next task"; bodyText: mainWindow.queueRowModel.length > 0 ? mainWindow.queueRowModel[0].name : "No queued task"; detailText: mainWindow.queueRowModel.length > 0 ? mainWindow.queueRowModel[0].nextRunText : "Use Quick create to add one"; accentColor: Theme.warning }
                CommandSummaryCard { titleText: "Active triggers"; bodyText: (controller.processTriggerActive || controller.networkTriggerActive) ? "Monitoring" : "No active trigger"; detailText: controller.processTriggerStatus + " · " + controller.networkTriggerStatus; accentColor: Theme.e5Pink }
                CommandSummaryCard { titleText: "Queue health"; bodyText: mainWindow.statusLabel(); detailText: String(mainWindow.queueRowModel.length) + " queued tasks"; accentColor: controller.statusColor }
            }

            // Existing quick create, task queue, trigger, script, settings, and recent activity sections stay below this point.
        }
    }
```

- [ ] **Step 4: Add local lightweight card components**

Before the closing `}` of `Window`, add these inline components if no reusable equivalent already exists:

```qml
    component StatusMiniCard: Rectangle {
        property string label: ""
        property string value: ""
        property color accentColor: Theme.primary
        Layout.fillWidth: true
        Layout.fillHeight: true
        radius: Theme.radiusMd
        color: Theme.glassSoft
        border.color: accentColor
        border.width: 1

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 4
            Text { text: label; color: Theme.textSecondary; font.pixelSize: 11; font.weight: Font.Bold }
            Text { text: value; color: accentColor; font.pixelSize: 14; font.weight: Font.Bold; elide: Text.ElideRight; Layout.fillWidth: true }
        }
    }

    component CommandSummaryCard: NeonCard {
        property string titleText: ""
        property string bodyText: ""
        property string detailText: ""
        property color accentColor: Theme.primary
        Layout.fillWidth: true
        Layout.fillHeight: true
        cardColor: Theme.cardGlass
        cardBorderColor: accentColor

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 6
            Text { text: titleText; color: accentColor; font.pixelSize: 12; font.weight: Font.Bold; font.letterSpacing: 1.1 }
            Text { text: bodyText; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold; elide: Text.ElideRight; Layout.fillWidth: true }
            Text { text: detailText; color: Theme.textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap; Layout.fillWidth: true; Layout.fillHeight: true }
        }
    }
```

- [ ] **Step 5: Run UI tests**

Run: `python -m unittest AutoShutdownQt.tests.test_e5e8_ui_regressions -v`

Expected: PASS after all old controller wiring snippets remain present and new 2.3 markers exist.

---

### Task 3: Move release identity to 2.3

**Files:**
- Modify: `AutoShutdownQt/main.py`
- Modify: `AutoShutdownQt/package_release.py`
- Create: `AutoShutdownQt/AutoShutdownQt-2.3.spec`
- Modify: `.gitignore`
- Modify: `AutoShutdownQt/tests/test_release_packaging.py`
- Test: `AutoShutdownQt/tests/test_release_packaging.py`

- [ ] **Step 1: Update release packaging tests to expect 2.3**

Change constants and assertions in `test_release_packaging.py` from `2.2` to `2.3`, including:

```python
SPEC = APP_DIR / "AutoShutdownQt-2.3.spec"
```

```python
def _valid_manifest(self, archive_name="AutoShutdownQt-2.3.zip", bundle="AutoShutdownQt-2.3"):
    return {
        "app": "AutoShutdownQt",
        "version": "2.3",
        "bundle": bundle,
        "executable": "AutoShutdownQt.exe",
        "archive": archive_name,
        "checks": {
            "executablePresent": True,
            "mainQmlPresent": True,
            "taskSchedulerIncluded": True,
        },
        "safetyNotes": [
            "Dry-run is enabled by default.",
            "Live mode can execute real Windows power actions.",
        ],
    }
```

Update archive paths written by `_write_valid_archive()` to `AutoShutdownQt-2.3/...`.

- [ ] **Step 2: Run failing packaging tests**

Run: `python -m unittest AutoShutdownQt.tests.test_release_packaging -v`

Expected: FAIL because package script, app version, spec, README, and release notes still identify 2.2.

- [ ] **Step 3: Update app version**

In `AutoShutdownQt/main.py`, change:

```python
app.setApplicationVersion("2.3")
```

- [ ] **Step 4: Update package script constants and checklist**

In `AutoShutdownQt/package_release.py`, change:

```python
VERSION = "2.3"
SPEC_FILE = APP_DIR / "AutoShutdownQt-2.3.spec"
APP_BUNDLE_DIR = DIST_DIR / "AutoShutdownQt-2.3"
ZIP_PATH = DIST_DIR / "AutoShutdownQt-2.3.zip"
RELEASE_CHECKLIST_PATH = DIST_DIR / "release-checklist-v2.3.md"
```

Change the checklist heading and bullets to:

```python
"# AutoShutdownQt 2.3 Release Checklist\n\n"
"- [ ] Launch app with Dry-run enabled by default.\n"
"- [ ] Verify Command Center safety strip shows dry-run/live state, action, tray, and queue count.\n"
"- [ ] Verify Next task, Active triggers, and Queue health cards are readable.\n"
"- [ ] Verify Task Queue Dashboard empty and populated states.\n"
"- [ ] Verify Recent activity shows logs and export/clear controls.\n"
"- [ ] Verify process/network trigger rows stay synchronized with monitors.\n"
"- [ ] Verify close-to-tray behavior when tray is available.\n"
"- [ ] Do not execute real shutdown, restart, sleep, hibernate, logoff, or lock during validation.\n"
"- [ ] Publish SHA256SUMS.txt next to the zip.\n"
```

- [ ] **Step 5: Create 2.3 spec from 2.2 spec**

Copy `AutoShutdownQt/AutoShutdownQt-2.2.spec` to `AutoShutdownQt/AutoShutdownQt-2.3.spec` and replace `AutoShutdownQt-2.2` with `AutoShutdownQt-2.3`.

- [ ] **Step 6: Allow 2.3 spec in gitignore**

Add this line to `.gitignore` next to the existing 2.2 exception:

```gitignore
!AutoShutdownQt/AutoShutdownQt-2.3.spec
```

- [ ] **Step 7: Run packaging tests**

Run: `python -m unittest AutoShutdownQt.tests.test_release_packaging -v`

Expected: PASS.

---

### Task 4: Update docs for 2.3 UI polish

**Files:**
- Modify: `README.md`
- Create: `RELEASE_NOTES_v2.3.md`
- Test: `AutoShutdownQt/tests/test_release_packaging.py`

- [ ] **Step 1: Update README current release text**

Change README heading/current release references to `AutoShutdownQt 2.3` and describe it as a command center UI polish release. Include these exact strings for tests:

```markdown
# AutoShutdownQt 2.3

AutoShutdownQt 2.3 is the current command center UI polish release.

- Download: `AutoShutdownQt-2.3.zip`
- Verify checksum with `SHA256SUMS.txt`
- Dry-run is enabled by default.
- The single-page Command Center highlights safety, queue health, triggers, and recent activity.
```

- [ ] **Step 2: Add release notes**

Create `RELEASE_NOTES_v2.3.md`:

```markdown
# AutoShutdownQt 2.3 Release Notes

AutoShutdownQt 2.3 是 AutoShutdownQt 2.2 stability release 之后的 command center UI polish release。它不改变调度语义，重点提升单页控制台的信息层级、安全状态可见性、任务队列可读性和日志可读性。

## 发布产物

- 便携版目录：`dist/AutoShutdownQt-2.3/`
- 便携版 zip：`dist/AutoShutdownQt-2.3.zip`
- 校验文件：`dist/SHA256SUMS.txt`
- 发布检查清单：`dist/release-checklist-v2.3.md`

## UI polish

- Single-page Command Center replaces the multi-page/sidebar workflow.
- Safety strip shows Dry-run/Live mode, current action, tray/background expectation, and queue count.
- Command cards highlight next task, active triggers, and queue health.
- Task Queue Dashboard improves queue readability without adding new scheduling behavior.
- Recent activity frames existing logs as an operational activity feed.

## 安全说明

- 默认开启 **Dry-run** 安全模式。
- Dry-run 下不会真实关机、重启、注销、锁定、睡眠或休眠。
- 验证时不要执行真实系统电源动作。
- 当前 exe **未做代码签名**，Windows 首次运行可能提示安全警告。
- 当前发布包是便携版，不是安装器。
```

- [ ] **Step 3: Update packaging tests for docs**

Ensure `test_release_packaging.py` checks `RELEASE_NOTES_v2.3.md`, `AutoShutdownQt 2.3`, `AutoShutdownQt-2.3.zip`, and `command center`.

- [ ] **Step 4: Run packaging tests**

Run: `python -m unittest AutoShutdownQt.tests.test_release_packaging -v`

Expected: PASS.

---

### Task 5: Full verification and package smoke check

**Files:**
- Test all changed files.

- [ ] **Step 1: Run full unit suite**

Run: `python -m unittest discover AutoShutdownQt/tests -v`

Expected: PASS.

- [ ] **Step 2: Build release package**

Run: `python AutoShutdownQt/package_release.py`

Expected output includes:

```text
Built AutoShutdownQt 2.3
Created archive: ...AutoShutdownQt-2.3.zip
Created checksum file: ...SHA256SUMS.txt
Created release checklist: ...release-checklist-v2.3.md
```

- [ ] **Step 3: Inspect generated artifacts**

Run:

```bash
python - <<'PY'
from pathlib import Path
import hashlib, zipfile
for p in [Path('dist/AutoShutdownQt-2.3.zip'), Path('dist/SHA256SUMS.txt'), Path('dist/release-checklist-v2.3.md')]:
    print(f'{p}: exists={p.exists()} size={p.stat().st_size if p.exists() else 0}')
zip_path = Path('dist/AutoShutdownQt-2.3.zip')
if zip_path.exists():
    print('sha256:', hashlib.sha256(zip_path.read_bytes()).hexdigest())
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        required = [n for n in names if n.endswith('AutoShutdownQt.exe') or n.endswith('release-manifest.json') or n.endswith('qml/Main.qml')]
        print('zip entries:', len(names))
        print('required entries:', *required, sep='\n  ')
PY
```

Expected: zip, checksum, checklist exist; archive contains exe, manifest, and Main.qml.

---

## Self-Review

- Spec coverage: The plan covers single-page command center, safety strip, command cards, task queue dashboard, recent activity, unchanged scheduling behavior, tests, release identity, README, release notes, checklist, and package validation.
- Placeholder scan: No TBD/TODO/fill-in placeholders remain.
- Type consistency: QML IDs and strings used by tests match the implementation steps: `commandCenterScroll`, `safetyStrip`, `commandCardsRow`, `taskQueueDashboard`, `Command Center`, `Task Queue Dashboard`, and `Recent activity`.
