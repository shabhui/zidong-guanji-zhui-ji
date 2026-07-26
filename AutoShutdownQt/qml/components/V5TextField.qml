import QtQuick
import QtQuick.Controls
import ".."

TextField {
    id: root

    implicitHeight: 38
    leftPadding: 12
    rightPadding: 12
    topPadding: 0
    bottomPadding: 0
    color: Theme.workspaceInk
    placeholderTextColor: Theme.workspaceMuted
    selectionColor: Theme.workspaceCyan
    selectedTextColor: Theme.workspaceBackground
    font.pixelSize: 12
    selectByMouse: true

    background: Rectangle {
        radius: Theme.controlRadius
        color: root.enabled ? Theme.inputGlass : Theme.workspaceSurfaceMuted
        border.color: root.activeFocus ? Theme.workspaceCyan : (root.hovered ? Theme.controlBorderHover : Theme.controlBorder)
        border.width: 1

        Behavior on border.color { ColorAnimation { duration: Theme.motionFast } }
    }
}
