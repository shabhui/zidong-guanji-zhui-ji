# AutoShutdownQt v2.0 e5e8 Reference Match Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild AutoShutdownQt v2.0 into an e5e8-reference-matched starry glass anime control deck while preserving the existing PySide6/QML controller logic and Dry-run safety.

**Architecture:** Keep the existing PySide6 app shell and `AppController` API. Add a self-contained right-side abstract anime visual component, expand theme tokens, upgrade reusable glass components, then replace the main QML composition with a large glass shell, neon title bar, glass rail navigation, central control deck, and page skins. Python business logic remains unchanged except for version/title text only if needed.

**Tech Stack:** Python 3, PySide6, Qt Quick/QML, Qt Quick Controls, existing QML component files in `AutoShutdownQt/qml/components/`.

---

## File Structure

### Files to modify

- `AutoShutdownQt/qml/Theme.qml`
  - Owns e5e8 color, spacing, radius, and animation tokens.
  - Add explicit semantic tokens so component code avoids scattered raw hex values.

- `AutoShutdownQt/qml/components/NeonCard.qml`
  - Owns reusable glass card visuals.
  - Add stronger e5e8 glass styling, active state, glow accents, and hover behavior.

- `AutoShutdownQt/qml/components/ActionTile.qml`
  - Owns power action tile visuals.
  - Make selected/hover states clearly neon and not color-only.

- `AutoShutdownQt/qml/components/FluentSwitch.qml`
  - Owns switch visual and click behavior.
  - Change off/on state to glass/neon style.

- `AutoShutdownQt/qml/Main.qml`
  - Owns application composition.
  - Rebuild background, shell, top bar, nav, overview, timer, action, trigger, and settings pages.

### Files to create

- `AutoShutdownQt/qml/components/StarryMascot.qml`
  - Self-contained abstract anime/starry visual panel for the right side of the overview page.
  - Uses only basic QML primitives: `Item`, `Rectangle`, `Repeater`, `Text`, gradients, opacity, rotation, and scale.
  - Does not import external images or depend on controller logic.

### Files not to modify

- `AutoShutdownQt/controller.py`
  - Preserve existing properties and slots: `dryRun`, `status`, `remainingText`, `targetInfo`, `selectedAction`, `forceClose`, `actionLabel`, `statusColor`, `startCountdown`, `startFixedTime`, `cancel`, `executeNow`.

- `AutoShutdownQt/power_service.py`
  - Preserve system action implementation.

- `build/`, `AutoShutdownQt/publish/`, zip files
  - Do not add to git.

---

## Task 1: Baseline Verification

**Files:**
- Read-only: `AutoShutdownQt/main.py`
- Read-only: `AutoShutdownQt/controller.py`
- Read-only: `AutoShutdownQt/power_service.py`
- Read-only: `AutoShutdownQt/qml/Main.qml`

- [ ] **Step 1: Check working tree before editing**

Run:

```bash
git -C /d/AIRUANJIAN status --short
```

Expected:

```text
?? AutoShutdownQt/current-render.png
?? AutoShutdownQt/e5e8b88f-7acc-4be7-930f-952ad1670984.png
```

If additional modified tracked files appear, inspect them before editing so unrelated user work is not overwritten.

- [ ] **Step 2: Run Python syntax baseline**

Run:

```bash
python -m py_compile AutoShutdownQt/main.py AutoShutdownQt/controller.py AutoShutdownQt/power_service.py
```

Expected: command exits with status `0` and prints no Python syntax errors.

- [ ] **Step 3: Record current QML component inventory**

Run:

```bash
git -C /d/AIRUANJIAN ls-files AutoShutdownQt/qml
```

Expected output includes at least:

```text
AutoShutdownQt/qml/Main.qml
AutoShutdownQt/qml/Theme.qml
AutoShutdownQt/qml/components/ActionTile.qml
AutoShutdownQt/qml/components/ConfirmDialog.qml
AutoShutdownQt/qml/components/FluentSwitch.qml
AutoShutdownQt/qml/components/NeonCard.qml
AutoShutdownQt/qml/components/SidebarItem.qml
AutoShutdownQt/qml/components/StatusHero.qml
AutoShutdownQt/qml/components/TimeInputPanel.qml
```

No commit is needed for this task.

---

## Task 2: Expand e5e8 Theme Tokens

**Files:**
- Modify: `AutoShutdownQt/qml/Theme.qml`

- [ ] **Step 1: Add semantic e5e8 tokens to `Theme.qml`**

Modify `AutoShutdownQt/qml/Theme.qml` so the `QtObject` contains these additional read-only properties after the existing text color properties:

```qml
    readonly property color e5BgA: "#090A1F"
    readonly property color e5BgB: "#111334"
    readonly property color e5BgC: "#1A1044"
    readonly property color e5Pink: "#FF6FD8"
    readonly property color e5Purple: "#9B5CFF"
    readonly property color e5Blue: "#4CC9FF"
    readonly property color e5Star: "#F7F2FF"

    readonly property color shellGlass: "#26101834"
    readonly property color cardGlass: "#30141B46"
    readonly property color cardGlassHover: "#421A255F"
    readonly property color cardGlassActive: "#522C1D68"
    readonly property color inputGlass: "#2AFFFFFF"

    readonly property color e5BorderSoft: "#55BDEBFF"
    readonly property color e5BorderStrong: "#B44CC9FF"
    readonly property color e5BorderPink: "#BBFF6FD8"
    readonly property color e5BorderPurple: "#AA9B5CFF"

    readonly property color glowBlue: "#554CC9FF"
    readonly property color glowPink: "#55FF6FD8"
    readonly property color glowPurple: "#559B5CFF"

    readonly property int floatVerySlow: 11200
    readonly property int twinkleSlow: 1800
```

Keep existing tokens such as `primary`, `secondary`, `accent`, `success`, `warning`, and `danger` for compatibility.

- [ ] **Step 2: Run Python syntax check**

Run:

```bash
python -m py_compile AutoShutdownQt/main.py AutoShutdownQt/controller.py AutoShutdownQt/power_service.py
```

Expected: command exits with status `0` and prints no Python syntax errors.

- [ ] **Step 3: Commit theme tokens**

Run:

```bash
git -C /d/AIRUANJIAN add AutoShutdownQt/qml/Theme.qml
git -C /d/AIRUANJIAN commit -m "Add v2.0 e5e8 QML theme tokens"
```

Expected: commit succeeds and only `AutoShutdownQt/qml/Theme.qml` is included.

---

## Task 3: Add Abstract Anime Visual Component

**Files:**
- Create: `AutoShutdownQt/qml/components/StarryMascot.qml`

- [ ] **Step 1: Create `StarryMascot.qml`**

Create `AutoShutdownQt/qml/components/StarryMascot.qml` with this complete content:

```qml
import QtQuick
import QtQuick.Layouts
import ".."

Item {
    id: root

    property string title: "星空守夜中"
    property string subtitle: "Sleep safely under the stars"
    property color accentColor: Theme.e5Pink

    implicitWidth: 286
    implicitHeight: 520

    Rectangle {
        anchors.fill: parent
        radius: Theme.radiusXl
        color: Theme.cardGlass
        border.color: Theme.e5BorderPurple
        border.width: 1
        opacity: 0.96
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: 1
        radius: Theme.radiusXl - 1
        gradient: Gradient {
            orientation: Gradient.Vertical
            GradientStop { position: 0.0; color: "#35FFFFFF" }
            GradientStop { position: 0.38; color: "#10101834" }
            GradientStop { position: 1.0; color: "#301A1044" }
        }
    }

    Rectangle {
        id: halo
        width: parent.width * 0.72
        height: width
        radius: width / 2
        anchors.horizontalCenter: parent.horizontalCenter
        y: 58
        color: Theme.glowPink
        opacity: 0.28
        scale: 1.0
        SequentialAnimation on scale {
            loops: Animation.Infinite
            NumberAnimation { from: 0.96; to: 1.04; duration: Theme.floatVerySlow; easing.type: Easing.InOutSine }
            NumberAnimation { from: 1.04; to: 0.96; duration: Theme.floatVerySlow; easing.type: Easing.InOutSine }
        }
    }

    Rectangle {
        width: parent.width * 0.48
        height: width
        radius: width / 2
        anchors.horizontalCenter: parent.horizontalCenter
        y: 92
        color: Theme.glowBlue
        opacity: 0.30
    }

    Rectangle {
        id: head
        width: 96
        height: 118
        radius: 48
        anchors.horizontalCenter: parent.horizontalCenter
        y: 128
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#90F7F2FF" }
            GradientStop { position: 0.48; color: "#88FF6FD8" }
            GradientStop { position: 1.0; color: "#559B5CFF" }
        }
        border.color: Theme.e5BorderPink
        border.width: 1
    }

    Rectangle {
        id: hairLeft
        width: 74
        height: 190
        radius: 36
        x: parent.width / 2 - 104
        y: 142
        rotation: -18
        color: "#669B5CFF"
        border.color: "#88FF6FD8"
        border.width: 1
    }

    Rectangle {
        id: hairRight
        width: 74
        height: 190
        radius: 36
        x: parent.width / 2 + 30
        y: 142
        rotation: 18
        color: "#664CC9FF"
        border.color: "#88FF6FD8"
        border.width: 1
    }

    Rectangle {
        id: shoulders
        width: parent.width * 0.68
        height: 126
        radius: 52
        anchors.horizontalCenter: parent.horizontalCenter
        y: 284
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#309B5CFF" }
            GradientStop { position: 0.5; color: "#66FF6FD8" }
            GradientStop { position: 1.0; color: "#304CC9FF" }
        }
        border.color: Theme.e5BorderPink
        border.width: 1
    }

    Repeater {
        model: 18
        Rectangle {
            width: index % 4 === 0 ? 4 : 3
            height: width
            radius: width / 2
            x: 24 + ((index * 37) % Math.max(1, root.width - 52))
            y: 28 + ((index * 53) % Math.max(1, root.height - 130))
            color: index % 3 === 0 ? Theme.e5Pink : (index % 3 === 1 ? Theme.e5Blue : Theme.e5Star)
            opacity: 0.30
            SequentialAnimation on opacity {
                loops: Animation.Infinite
                PauseAnimation { duration: index * 70 }
                NumberAnimation { from: 0.16; to: 0.72; duration: Theme.twinkleSlow + index * 18; easing.type: Easing.InOutSine }
                NumberAnimation { from: 0.72; to: 0.16; duration: Theme.twinkleSlow + index * 14; easing.type: Easing.InOutSine }
            }
        }
    }

    ColumnLayout {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 24
        spacing: 6

        Text {
            Layout.fillWidth: true
            text: root.title
            color: Theme.textPrimary
            font.pixelSize: 22
            font.weight: Font.Bold
            horizontalAlignment: Text.AlignHCenter
        }

        Text {
            Layout.fillWidth: true
            text: root.subtitle
            color: Theme.textSecondary
            font.pixelSize: 12
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
        }
    }
}
```

- [ ] **Step 2: Verify no external image dependency was introduced**

Run:

```bash
git -C /d/AIRUANJIAN diff -- AutoShutdownQt/qml/components/StarryMascot.qml
```

Expected: diff shows only QML primitives and no `Image { ... }` element.

- [ ] **Step 3: Commit the mascot component**

Run:

```bash
git -C /d/AIRUANJIAN add AutoShutdownQt/qml/components/StarryMascot.qml
git -C /d/AIRUANJIAN commit -m "Add v2.0 starry mascot component"
```

Expected: commit succeeds and creates one new QML file.

---

## Task 4: Upgrade Shared Glass Components

**Files:**
- Modify: `AutoShutdownQt/qml/components/NeonCard.qml`
- Modify: `AutoShutdownQt/qml/components/ActionTile.qml`
- Modify: `AutoShutdownQt/qml/components/FluentSwitch.qml`

- [ ] **Step 1: Extend `NeonCard.qml` properties**

Modify the property block in `AutoShutdownQt/qml/components/NeonCard.qml` so it includes:

```qml
    property color cardBorderColor: Theme.e5BorderSoft
    property color cardColor: Theme.cardGlass
    property color hoverColor: Theme.cardGlassHover
    property bool hoverable: true
    property bool breathing: false
    property bool active: false
    property color activeBorderColor: Theme.e5BorderPink
```

- [ ] **Step 2: Update `NeonCard.qml` state expressions**

Update the root `Rectangle` visual expressions to:

```qml
    color: active ? Theme.cardGlassActive : (hoverArea.containsMouse && hoverable ? hoverColor : cardColor)
    radius: Theme.radiusLg
    border.color: active ? activeBorderColor : (hoverArea.containsMouse && hoverable ? Theme.e5BorderStrong : cardBorderColor)
    border.width: active ? 2 : 1
    antialiasing: true
    scale: hoverArea.containsMouse && hoverable ? 1.008 : 1.0
```

- [ ] **Step 3: Update `NeonCard.qml` glow colors**

Change the first corner glow color to `Theme.e5Blue` and the second corner glow color to `Theme.e5Pink`. Keep their hover opacity behavior.

Expected result: card hover and active states are stronger, but existing callers that only set `cardColor` and `cardBorderColor` still work.

- [ ] **Step 4: Update `ActionTile.qml` selected state**

Modify `AutoShutdownQt/qml/components/ActionTile.qml` so selected tiles use the new active state:

```qml
    active: isSelected
    cardColor: isSelected ? Theme.cardGlassActive : Theme.cardGlass
    hoverColor: isSelected ? "#66301F78" : Theme.cardGlassHover
    cardBorderColor: isSelected ? Theme.e5BorderPink : Theme.e5BorderSoft
    activeBorderColor: Theme.e5BorderPink
    scale: mouseArea.containsMouse ? 1.025 : 1.0
```

Also set the selected left indicator color to `Theme.e5Pink` and the selected overlay color to `Theme.glowBlue`.

- [ ] **Step 5: Update `FluentSwitch.qml` colors**

Modify `AutoShutdownQt/qml/components/FluentSwitch.qml` so the switch background and knob use e5e8 tokens:

```qml
        color: root.checked ? Theme.glowBlue : Theme.inputGlass
        border.color: root.checked ? Theme.e5BorderStrong : Theme.e5BorderSoft
```

Change knob color to:

```qml
            color: root.checked ? Theme.e5Star : Theme.textSecondary
```

- [ ] **Step 6: Run Python syntax check**

Run:

```bash
python -m py_compile AutoShutdownQt/main.py AutoShutdownQt/controller.py AutoShutdownQt/power_service.py
```

Expected: command exits with status `0` and prints no Python syntax errors.

- [ ] **Step 7: Commit shared component upgrades**

Run:

```bash
git -C /d/AIRUANJIAN add AutoShutdownQt/qml/components/NeonCard.qml AutoShutdownQt/qml/components/ActionTile.qml AutoShutdownQt/qml/components/FluentSwitch.qml
git -C /d/AIRUANJIAN commit -m "Upgrade v2.0 e5e8 glass components"
```

Expected: commit succeeds and only the three component files are included.

---

## Task 5: Rebuild Main Shell, Top Bar, and Navigation

**Files:**
- Modify: `AutoShutdownQt/qml/Main.qml`

- [ ] **Step 1: Update window title and page model**

In `AutoShutdownQt/qml/Main.qml`, update:

```qml
    title: "AutoShutdown v2.0"
```

Replace the pages array with:

```qml
    readonly property var pages: ["总览", "定时", "任务", "智能触发", "脚本", "设置"]
```

Keep `currentPage`, `topBarHeight`, `sidebarWidth`, and `outerMargin` properties.

- [ ] **Step 2: Replace the base background gradient**

Replace the first background `Rectangle` gradient with:

```qml
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: Theme.e5BgA }
            GradientStop { position: 0.46; color: Theme.e5BgB }
            GradientStop { position: 1.0; color: Theme.e5BgC }
        }
    }
```

- [ ] **Step 3: Update floating orb colors**

In the existing orb rectangles, use these colors:

```qml
        color: Theme.e5Purple
```

```qml
        color: Theme.e5Blue
```

```qml
        color: Theme.e5Pink
```

```qml
        color: Theme.e5Purple
```

Use `Theme.floatVerySlow` where the current code uses `Theme.floatSlow` for large background orb animations.

- [ ] **Step 4: Add a glass shell behind sidebar and content**

Add this `NeonCard` after the star `Repeater` and before the title bar:

```qml
    NeonCard {
        id: appShell
        x: outerMargin - 8
        y: topBarHeight + outerMargin - 8
        width: parent.width - outerMargin * 2 + 16
        height: parent.height - topBarHeight - outerMargin * 2 + 16
        radius: Theme.radiusXl
        cardColor: Theme.shellGlass
        cardBorderColor: Theme.e5BorderSoft
        hoverable: false
        z: 0
    }
```

Set `sidebar` and `contentHost` to `z: 1` if needed so they render above the shell.

- [ ] **Step 5: Update title bar subtitle and icon**

In the title bar:

- Replace the icon text `⏻` with a non-emoji text mark such as `AS`.
- Replace subtitle text with:

```qml
                    text: "v2.0 · Starry Glass"
```

- Add a `DRY RUN` pill near the status pill with:

```qml
            Rectangle {
                Layout.preferredWidth: dryRunText.implicitWidth + 24
                Layout.preferredHeight: 30
                radius: 15
                color: controller.dryRun ? "#2262F6B5" : "#22FF5C8A"
                border.color: controller.dryRun ? Theme.success : Theme.danger
                border.width: 1
                Text {
                    id: dryRunText
                    anchors.centerIn: parent
                    text: controller.dryRun ? "DRY RUN" : "LIVE MODE"
                    color: controller.dryRun ? Theme.success : Theme.danger
                    font.pixelSize: 12
                    font.weight: Font.Bold
                }
            }
```

- [ ] **Step 6: Update sidebar card and navigation active style**

In the `sidebar` `NeonCard`, set:

```qml
        cardColor: Theme.shellGlass
        cardBorderColor: Theme.e5BorderSoft
```

In each nav delegate:

```qml
                    color: currentPage === index ? Theme.cardGlassActive : "transparent"
                    border.color: currentPage === index ? Theme.e5BorderPink : "transparent"
```

Set active indicator color to `Theme.e5Blue` or `Theme.e5Pink`.

- [ ] **Step 7: Run Python syntax check**

Run:

```bash
python -m py_compile AutoShutdownQt/main.py AutoShutdownQt/controller.py AutoShutdownQt/power_service.py
```

Expected: command exits with status `0` and prints no Python syntax errors.

- [ ] **Step 8: Commit shell/navigation changes**

Run:

```bash
git -C /d/AIRUANJIAN add AutoShutdownQt/qml/Main.qml
git -C /d/AIRUANJIAN commit -m "Rebuild v2.0 e5e8 shell navigation"
```

Expected: commit succeeds and only `AutoShutdownQt/qml/Main.qml` is included.

---

## Task 6: Rebuild Overview Page with Three-Column e5e8 Composition

**Files:**
- Modify: `AutoShutdownQt/qml/Main.qml`
- Use: `AutoShutdownQt/qml/components/StarryMascot.qml`

- [ ] **Step 1: Replace overview root layout with `RowLayout`**

Inside the overview page `Item { visible: currentPage === 0 }`, replace the current single `ColumnLayout` with a `RowLayout` that has a central `ColumnLayout` and a right `StarryMascot`:

```qml
            RowLayout {
                anchors.fill: parent
                spacing: 18

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 16

                    // Keep hero card, shortcut cards, and action grid here.
                }

                StarryMascot {
                    Layout.preferredWidth: 286
                    Layout.fillHeight: true
                    title: "星空守夜中"
                    subtitle: controller.dryRun ? "Dry-run safety mode" : "Live power mode enabled"
                }
            }
```

- [ ] **Step 2: Restyle overview hero card**

In the hero card, set:

```qml
                    cardColor: Theme.cardGlassActive
                    cardBorderColor: Theme.e5BorderPink
                    active: true
                    activeBorderColor: Theme.e5BorderPink
                    breathing: true
```

Keep existing texts bound to `controller.actionLabel`, `controller.remainingText`, `controller.targetInfo`, and `mainWindow.statusLabel()`.

- [ ] **Step 3: Update primary CTA text**

Change the hero primary button text from:

```qml
                                text: "启动 30 分钟倒计时"
```

to:

```qml
                                text: "启动倒计时"
```

Keep its current safe behavior:

```qml
                                onClicked: controller.startCountdown(0, 30, 0)
```

- [ ] **Step 4: Keep dangerous action as secondary**

Keep `立即执行当前动作` as a separate button that opens `confirmDialog`. Do not call `controller.executeNow()` directly from the overview page.

Expected code remains:

```qml
                                text: "立即执行当前动作"
                                onClicked: confirmDialog.open()
```

- [ ] **Step 5: Restyle shortcut and configuration cards**

For overview shortcut and configuration cards, use:

```qml
                        cardColor: Theme.cardGlass
                        cardBorderColor: Theme.e5BorderSoft
```

For the Dry-run configuration text, preserve the color logic:

```qml
color: controller.dryRun ? Theme.success : Theme.danger
```

- [ ] **Step 6: Run Python syntax check**

Run:

```bash
python -m py_compile AutoShutdownQt/main.py AutoShutdownQt/controller.py AutoShutdownQt/power_service.py
```

Expected: command exits with status `0` and prints no Python syntax errors.

- [ ] **Step 7: Commit overview composition**

Run:

```bash
git -C /d/AIRUANJIAN add AutoShutdownQt/qml/Main.qml
git -C /d/AIRUANJIAN commit -m "Add v2.0 e5e8 overview composition"
```

Expected: commit succeeds and only `AutoShutdownQt/qml/Main.qml` is included.

---

## Task 7: Skin Timer, Action, Trigger, Script, and Settings Pages

**Files:**
- Modify: `AutoShutdownQt/qml/Main.qml`

- [ ] **Step 1: Rename page comments to match the new page model**

Update page comments and visibility indices so they match:

```text
0 总览
1 定时
2 任务
3 智能触发
4 脚本
5 设置
```

The old `Actions page` at `currentPage === 2` becomes the `任务` page if no task business logic exists yet. It should explain that task migration is pending while keeping action selection available on the overview page and action tiles.

- [ ] **Step 2: Restyle timer page cards**

In the timer page cards, set:

```qml
                    cardColor: Theme.cardGlass
                    cardBorderColor: Theme.e5BorderSoft
```

Keep the existing `TimeInputPanel` ids and `controller.startCountdown(...)` / `controller.startFixedTime(...)` calls.

- [ ] **Step 3: Replace the old actions page with a task migration note card**

For `currentPage === 2`, use a `NeonCard` with text:

```qml
Text { text: "任务中心"; color: Theme.textPrimary; font.pixelSize: 26; font.weight: Font.Bold }
Text {
    Layout.fillWidth: true
    text: "v2.0 先保留核心倒计时与动作执行。任务模板会复用旧版已验证规则迁移到 QML。"
    color: Theme.textSecondary
    font.pixelSize: 14
    wrapMode: Text.WordWrap
}
```

Also include a compact action tile grid in this page only if it does not duplicate controls awkwardly. If included, use the same six `ActionTile` declarations as the overview page.

- [ ] **Step 4: Restyle trigger page as two accordion-like cards**

For `currentPage === 3`, replace the single migration note card content with two nested `NeonCard` sections:

```qml
Text { text: "智能触发"; color: Theme.textPrimary; font.pixelSize: 26; font.weight: Font.Bold }
NeonCard {
    Layout.fillWidth: true
    Layout.preferredHeight: 156
    cardColor: Theme.cardGlass
    cardBorderColor: Theme.e5BorderPink
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 8
        Text { text: "网络闲置触发"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
        Text { text: "下载/上传速度持续低于阈值后执行当前电源动作。高级逻辑将在后续迁移。"; color: Theme.textSecondary; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
        Text { text: "状态：待迁移"; color: Theme.e5Blue; font.pixelSize: 13; font.weight: Font.Bold }
    }
}
NeonCard {
    Layout.fillWidth: true
    Layout.preferredHeight: 156
    cardColor: Theme.cardGlass
    cardBorderColor: Theme.e5BorderPurple
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 8
        Text { text: "进程退出触发"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
        Text { text: "监控程序退出后执行当前电源动作，自动关闭子面板将在后续迁移。"; color: Theme.textSecondary; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
        Text { text: "状态：待迁移"; color: Theme.e5Pink; font.pixelSize: 13; font.weight: Font.Bold }
    }
}
```

This keeps the visual requirement without inventing controller APIs that do not exist.

- [ ] **Step 5: Add script page at `currentPage === 4`**

Create a script page `Item` using one `NeonCard` with:

```qml
Text { text: "执行前脚本"; color: Theme.textPrimary; font.pixelSize: 26; font.weight: Font.Bold }
Text {
    Layout.fillWidth: true
    text: "脚本路径、启用状态和超时设置将在业务逻辑迁移后接入。当前版本保持 Dry-run 安全验证。"
    color: Theme.textSecondary
    font.pixelSize: 14
    wrapMode: Text.WordWrap
}
Text { text: "状态：未启用"; color: Theme.warning; font.pixelSize: 14; font.weight: Font.Bold }
```

Use `cardColor: Theme.cardGlass` and `cardBorderColor: Theme.e5BorderSoft`.

- [ ] **Step 6: Move settings page visibility to `currentPage === 5`**

Change the existing settings page from:

```qml
visible: currentPage === 4
```

to:

```qml
visible: currentPage === 5
```

Set its `NeonCard` to:

```qml
                cardColor: Theme.cardGlass
                cardBorderColor: Theme.e5BorderSoft
```

Keep both existing switches:

```qml
FluentSwitch { checked: controller.dryRun; onCheckedChanged: controller.dryRun = checked }
FluentSwitch { checked: controller.forceClose; onCheckedChanged: controller.forceClose = checked }
```

- [ ] **Step 7: Run Python syntax check**

Run:

```bash
python -m py_compile AutoShutdownQt/main.py AutoShutdownQt/controller.py AutoShutdownQt/power_service.py
```

Expected: command exits with status `0` and prints no Python syntax errors.

- [ ] **Step 8: Commit page skin changes**

Run:

```bash
git -C /d/AIRUANJIAN add AutoShutdownQt/qml/Main.qml
git -C /d/AIRUANJIAN commit -m "Skin v2.0 e5e8 secondary pages"
```

Expected: commit succeeds and only `AutoShutdownQt/qml/Main.qml` is included.

---

## Task 8: Runtime Verification and Screenshot

**Files:**
- Runtime only: `AutoShutdownQt/main.py`
- Runtime only: `AutoShutdownQt/qml/Main.qml`
- Ignored/untracked output: `AutoShutdownQt/current-render.png`

- [ ] **Step 1: Run Python syntax verification**

Run:

```bash
python -m py_compile AutoShutdownQt/main.py AutoShutdownQt/controller.py AutoShutdownQt/power_service.py
```

Expected: command exits with status `0` and prints no Python syntax errors.

- [ ] **Step 2: Launch the app**

Run:

```bash
python AutoShutdownQt/main.py
```

Expected:

- App opens without QML startup failure.
- No terminal output containing these critical strings:

```text
ReferenceError
TypeError
is not a type
Cannot assign
```

- [ ] **Step 3: Visual acceptance checklist**

Compare the running app against `AutoShutdownQt/e5e8b88f-7acc-4be7-930f-952ad1670984.png` and confirm:

- Background is pink/purple/blue starry glass, not gray.
- A large translucent shell frames the application.
- Top bar says `AutoShutdown` and `v2.0 · Starry Glass`.
- There is a `DRY RUN` or `LIVE MODE` pill.
- Left navigation is a glass rail with an obvious active item.
- Overview page has a central control area and a right abstract anime/starry visual panel.
- Right visual panel does not use a real image.
- No large pure gray blocks dominate the UI.

- [ ] **Step 4: Save or update screenshot**

If a screenshot workflow already exists, update `AutoShutdownQt/current-render.png`. Keep it untracked unless the user explicitly asks to commit screenshots.

- [ ] **Step 5: Check git status**

Run:

```bash
git -C /d/AIRUANJIAN status --short
```

Expected tracked files are clean after commits. Untracked screenshots may remain:

```text
?? AutoShutdownQt/current-render.png
?? AutoShutdownQt/e5e8b88f-7acc-4be7-930f-952ad1670984.png
```

No commit is required unless verification reveals a fix.

---

## Task 9: Final Review and Optional Release

**Files:**
- Read-only: git diff/status
- Optional release output: `AutoShutdownQt-v2.0-win-x64.zip`

- [ ] **Step 1: Run final diff review**

Run:

```bash
git -C /d/AIRUANJIAN log --oneline -6
git -C /d/AIRUANJIAN status --short
```

Expected:

- Recent commits include the e5e8 design and implementation commits.
- No tracked modified files remain.
- `build/`, publish directories, and zip files are not staged.

- [ ] **Step 2: Request code review before release**

Use the `requesting-code-review` skill or `code-review` skill before publishing. Review focus:

- QML startup correctness.
- No invented controller APIs.
- Dry-run safety preserved.
- No external image dependency.
- e5e8 visual requirements covered.

- [ ] **Step 3: Release only after explicit publish direction**

If the user explicitly asks to publish v2.0, create a release artifact named:

```text
AutoShutdownQt-v2.0-win-x64.zip
```

Use GitHub Release tag:

```text
v2.0
```

Release title:

```text
AutoShutdownQt v2.0
```

Release notes:

```text
AutoShutdownQt v2.0 更新：高度参考 e5e8 视觉图重做 UI，加入粉紫蓝星空背景、大面积毛玻璃控制台、右侧抽象 anime 视觉位与更强的霓虹组件状态；保留现有 Dry-run 与电源动作安全逻辑。
```

Do not commit or upload `build/` as repository content.

---

## Self-Review

### Spec coverage

- e5e8 reference match: covered by Tasks 2, 5, 6, 7, 8.
- Pink/purple/blue starry background: covered by Tasks 2 and 5.
- Large glass shell: covered by Task 5.
- Glass rail navigation: covered by Task 5.
- Right abstract anime visual without image dependency: covered by Task 3 and Task 6.
- Main control area and CTA hierarchy: covered by Task 6.
- Glass card/button/tile/switch styling: covered by Task 4.
- Secondary pages styled without inventing unavailable business APIs: covered by Task 7.
- Dry-run safety and Python logic preservation: covered by Tasks 1, 7, 8, 9.
- No build/publish/zip commits: covered by Tasks 8 and 9.

### Placeholder scan

This plan has no open-marker phrases and no unspecified implementation sections. Places where business logic does not yet exist are handled as explicit visual migration note cards with exact text, avoiding invented controller APIs.

### Type and property consistency

- Theme properties added in Task 2 are referenced consistently in Tasks 3–7.
- `StarryMascot.qml` created in Task 3 is referenced by `Main.qml` in Task 6 through the existing `import "components"` line.
- Existing controller properties and slots are preserved and referenced by their current names.
- Page indices are updated consistently to `["总览", "定时", "任务", "智能触发", "脚本", "设置"]`.
