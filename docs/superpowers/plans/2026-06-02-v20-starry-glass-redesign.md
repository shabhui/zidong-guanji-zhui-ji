# AutoShutdownQt v2.0 Starry Glass Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current grey-box AutoShutdownQt v2.0-preview visual layer with an anime-inspired starry glassmorphism UI with subtle animations.

**Architecture:** Preserve the existing PySide6/QML project and `AppController` logic. Update QML theme tokens, card/tile components, and `Main.qml` decorative/background layers while keeping the stable topbar/sidebar/content layout. Validate with Python compilation and offscreen QML loading.

**Tech Stack:** Python 3.12, PySide6 6.11, Qt Quick/QML, Qt Quick Layouts.

---

## File Structure

- Modify `AutoShutdownQt/qml/Theme.qml`
  - Add anime starry glass colors, glass surfaces, glow colors, and animation durations.
- Modify `AutoShutdownQt/qml/components/NeonCard.qml`
  - Convert basic cards into reusable animated glass cards with highlight overlay and hover state.
- Modify `AutoShutdownQt/qml/components/ActionTile.qml`
  - Strengthen selected/hover visuals and remove grey-box feeling.
- Modify `AutoShutdownQt/qml/components/FluentSwitch.qml`
  - Align switch colors with starry glass theme.
- Modify `AutoShutdownQt/qml/Main.qml`
  - Replace grey panels with starry background, floating orbs, animated stars, and glass panels.

---

### Task 1: Upgrade theme and glass components

**Files:**
- Modify: `AutoShutdownQt/qml/Theme.qml`
- Modify: `AutoShutdownQt/qml/components/NeonCard.qml`
- Modify: `AutoShutdownQt/qml/components/ActionTile.qml`
- Modify: `AutoShutdownQt/qml/components/FluentSwitch.qml`

- [ ] **Step 1: Replace Theme.qml with starry glass tokens**

Write `AutoShutdownQt/qml/Theme.qml` with semantic colors:

```qml
pragma Singleton
import QtQuick

QtObject {
    readonly property color bgDeep: "#070A1A"
    readonly property color bgNight: "#101437"
    readonly property color bgViolet: "#25114A"
    readonly property color glassBase: "#24FFFFFF"
    readonly property color glassSoft: "#18FFFFFF"
    readonly property color glassStrong: "#36FFFFFF"
    readonly property color glassHover: "#46FFFFFF"
    readonly property color borderSoft: "#40BDEBFF"
    readonly property color borderStrong: "#9AE6FFFF"
    readonly property color borderPink: "#AAFF8ACF"
    readonly property color primary: "#79D8FF"
    readonly property color secondary: "#B779FF"
    readonly property color accent: "#FF8ACF"
    readonly property color success: "#7DFFC4"
    readonly property color warning: "#FFD166"
    readonly property color danger: "#FF5C8A"
    readonly property color textPrimary: "#FFF7FF"
    readonly property color textSecondary: "#D9CCF3"
    readonly property real radiusSm: 10
    readonly property real radiusMd: 16
    readonly property real radiusLg: 22
    readonly property real radiusXl: 30
    readonly property real spaceXs: 4
    readonly property real spaceSm: 8
    readonly property real spaceMd: 16
    readonly property real spaceLg: 24
    readonly property real spaceXl: 32
    readonly property int animFast: 130
    readonly property int animNormal: 240
    readonly property int animSlow: 420
    readonly property int floatSlow: 7600
}
```

- [ ] **Step 2: Replace NeonCard.qml with animated glass card**

Write `AutoShutdownQt/qml/components/NeonCard.qml`:

```qml
import QtQuick
import ".."

Rectangle {
    id: root
    property color cardBorderColor: Theme.borderSoft
    property color cardColor: Theme.glassBase
    property color hoverColor: Theme.glassHover
    property bool hoverable: true

    color: mouseArea.containsMouse && hoverable ? hoverColor : cardColor
    radius: Theme.radiusLg
    border.color: mouseArea.containsMouse && hoverable ? Theme.borderStrong : cardBorderColor
    border.width: 1
    antialiasing: true

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: Math.max(24, parent.height * 0.28)
        radius: parent.radius
        color: "#22FFFFFF"
        opacity: 0.8
    }

    Rectangle {
        width: 90
        height: 90
        radius: 45
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.rightMargin: -24
        anchors.topMargin: -32
        color: Theme.primary
        opacity: mouseArea.containsMouse && hoverable ? 0.16 : 0.08
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
    }

    Behavior on color { ColorAnimation { duration: Theme.animNormal } }
    Behavior on border.color { ColorAnimation { duration: Theme.animNormal } }
}
```

- [ ] **Step 3: Replace ActionTile.qml selected/hover visuals**

Write `AutoShutdownQt/qml/components/ActionTile.qml`:

```qml
import QtQuick
import QtQuick.Layouts
import ".."

NeonCard {
    id: root
    implicitHeight: 78
    hoverable: true

    property string actionKey: ""
    property string actionLabel: ""
    property string actionSub: ""
    property bool isSelected: controller.selectedAction === actionKey

    cardColor: isSelected ? "#40FF8ACF" : "#20FFFFFF"
    hoverColor: isSelected ? "#52FF8ACF" : "#34FFFFFF"
    cardBorderColor: isSelected ? Theme.borderPink : Theme.borderSoft
    scale: mouseArea.containsMouse ? 1.025 : 1.0

    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 4
        radius: 2
        color: root.isSelected ? Theme.accent : "transparent"
        opacity: root.isSelected ? 1 : 0
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: controller.selectedAction = root.actionKey
    }

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 4
        Text {
            text: actionLabel
            color: root.isSelected ? Theme.textPrimary : Theme.textSecondary
            font.pixelSize: 16
            font.weight: Font.Bold
            Layout.alignment: Qt.AlignHCenter
        }
        Text {
            text: actionSub
            color: root.isSelected ? Theme.primary : Theme.textSecondary
            font.pixelSize: 10
            opacity: root.isSelected ? 1 : 0.72
            Layout.alignment: Qt.AlignHCenter
        }
    }

    Behavior on scale { NumberAnimation { duration: Theme.animFast } }
}
```

- [ ] **Step 4: Update FluentSwitch colors**

In `AutoShutdownQt/qml/components/FluentSwitch.qml`, replace colors with starry tokens:

```qml
color: root.checked ? Theme.primary : "#24304D"
border.color: root.checked ? Theme.borderStrong : Theme.borderSoft
```

- [ ] **Step 5: Validate QML load**

Run the offscreen QML load command from Task 3 Step 1 below.

Expected: `AutoShutdownQt starry QML load OK`.

---

### Task 2: Rework Main.qml starry background and glass surfaces

**Files:**
- Modify: `AutoShutdownQt/qml/Main.qml`

- [ ] **Step 1: Replace grey colors with starry tokens**

In `Main.qml`, replace panel colors like `#10182B`, `#2022334A`, `#22FFFFFF`, and `#2BFFFFFF` with theme glass tokens:

```qml
color: Theme.glassSoft
cardColor: Theme.glassBase
cardBorderColor: Theme.borderSoft
```

For the hero card use:

```qml
cardColor: "#34FFFFFF"
cardBorderColor: Theme.borderStrong
```

- [ ] **Step 2: Add animated floating orbs**

Replace the static neon rectangles at the top of `Main.qml` with four animated orbs using `SequentialAnimation on x/y` and opacity 0.08–0.18. Use cyan, purple, pink, and violet.

- [ ] **Step 3: Add star sparkle layer**

Add a `Repeater` with 36 small circular `Rectangle` stars. Use deterministic positions from index formulas and animate `opacity` with staggered `SequentialAnimation`.

- [ ] **Step 4: Make title bar and sidebar glassy**

Use `NeonCard` or transparent rectangles for title/sidebar surfaces, with `Theme.glassSoft`, `Theme.borderSoft`, and active nav `Theme.glassStrong`.

- [ ] **Step 5: Add hero breathing animation**

On the hero `NeonCard`, animate `scale` between 1 and 1.006 or animate a decorative glow circle opacity. Keep it subtle.

---

### Task 3: Validate and commit

**Files:**
- Modified QML files only.

- [ ] **Step 1: Run Python and QML validation**

Run:

```bash
python -m py_compile AutoShutdownQt/main.py AutoShutdownQt/controller.py AutoShutdownQt/power_service.py
python - <<'PY'
import os, sys
from pathlib import Path
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from PySide6.QtCore import QTimer, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
sys.path.insert(0, str(Path('AutoShutdownQt').resolve()))
from controller import AppController
messages=[]
def handler(mode, context, message):
    if any(k in message for k in ['failed', 'Error', 'ReferenceError', 'is not a type', 'Cannot assign', 'Cannot override', 'Unable to assign', 'TypeError', 'Cannot specify']):
        messages.append(f'{context.file}:{context.line}: {message}')
qInstallMessageHandler(handler)
try:
    QQuickStyle.setStyle('Fusion')
except Exception:
    pass
app = QGuiApplication([])
engine = QQmlApplicationEngine()
controller = AppController()
engine.rootContext().setContextProperty('controller', controller)
qml_dir = Path('AutoShutdownQt/qml').resolve()
engine.addImportPath(str(qml_dir))
engine.load(str(qml_dir / 'Main.qml'))
if not engine.rootObjects():
    print('\n'.join(messages))
    raise SystemExit('QML load failed')
if messages:
    print('\n'.join(messages))
    raise SystemExit('QML relevant warnings found')
QTimer.singleShot(500, app.quit)
app.exec()
print('AutoShutdownQt starry QML load OK')
PY
```

Expected: `AutoShutdownQt starry QML load OK`.

- [ ] **Step 2: Manual launch**

Run:

```bash
python AutoShutdownQt/main.py
```

Expected: window opens with starry anime glass UI, no large grey boxes, animated orbs/stars visible.

- [ ] **Step 3: Commit**

Run:

```bash
git add AutoShutdownQt/qml/Theme.qml AutoShutdownQt/qml/Main.qml AutoShutdownQt/qml/components/NeonCard.qml AutoShutdownQt/qml/components/ActionTile.qml AutoShutdownQt/qml/components/FluentSwitch.qml
git commit -m "Add starry glass anime QML visuals"
```

---

## Self-Review Notes

- Spec coverage: Theme tokens, glass cards, animated background, star particles, hero animation, action tile hover/selected states, and dry-run preservation are covered.
- Placeholder scan: no TBD/TODO/FIXME placeholders.
- Type consistency: `Theme.glassBase`, `Theme.glassSoft`, `Theme.glassStrong`, `Theme.glassHover`, `Theme.borderPink`, and `Theme.floatSlow` are introduced before use.
