import QtQuick
import ".."

Item {
    id: root
    width: 48; height: 28
    property bool checked: false
    scale: switchMouse.pressed ? 0.96 : (switchMouse.containsMouse ? 1.02 : 1.0)

    Behavior on scale { NumberAnimation { duration: Theme.motionFast; easing.type: Easing.OutCubic } }

    Rectangle {
        anchors.fill: parent
        radius: 14
        color: root.checked ? Theme.checkedTrack : Theme.inputGlass
        border.color: root.checked ? Theme.e5BorderStrong : Theme.e5BorderSoft
        border.width: 1

        Behavior on color { ColorAnimation { duration: Theme.motionFast; easing.type: Easing.OutCubic } }
        Behavior on border.color { ColorAnimation { duration: Theme.motionFast; easing.type: Easing.OutCubic } }

        Rectangle {
            width: 22; height: 22
            radius: 11
            color: root.checked ? Theme.e5Star : Theme.textSecondary
            anchors.verticalCenter: parent.verticalCenter
            x: root.checked ? parent.width - width - 3 : 3
            Behavior on x { NumberAnimation { duration: Theme.motionFast; easing.type: Easing.OutCubic } }
            Behavior on color { ColorAnimation { duration: Theme.motionFast; easing.type: Easing.OutCubic } }
        }

        MouseArea {
            id: switchMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: root.checked = !root.checked
        }
    }
}
