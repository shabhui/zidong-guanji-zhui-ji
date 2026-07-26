import QtQuick
import QtQuick.Controls
import ".."

Slider {
    id: root

    property color accentColor: Theme.workspaceCyan

    implicitWidth: 190
    implicitHeight: 30
    hoverEnabled: true
    snapMode: Slider.SnapAlways

    background: Rectangle {
        x: root.leftPadding
        y: root.topPadding + root.availableHeight / 2 - height / 2
        width: root.availableWidth
        height: 4
        radius: 2
        color: Theme.workspaceSurfaceMuted
        border.color: Theme.controlBorder
        border.width: 1

        Rectangle {
            width: root.visualPosition * parent.width
            height: parent.height
            radius: parent.radius
            color: root.accentColor
        }
    }

    handle: Rectangle {
        x: root.leftPadding + root.visualPosition * (root.availableWidth - width)
        y: root.topPadding + (root.availableHeight - height) / 2
        implicitWidth: 18
        implicitHeight: 18
        radius: 9
        color: root.pressed ? Qt.lighter(root.accentColor, 1.14) : root.accentColor
        border.color: Theme.workspaceInk
        border.width: 2

        Rectangle {
            anchors.centerIn: parent
            width: 5
            height: 5
            radius: 2.5
            color: Theme.workspaceBackground
        }

        Behavior on color { ColorAnimation { duration: Theme.motionFast } }
    }
}
