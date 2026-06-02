import QtQuick
import ".."

Item {
    id: root
    width: 48; height: 28
    property bool checked: false

    Rectangle {
        anchors.fill: parent
        radius: 14
        color: root.checked ? Theme.glowBlue : Theme.inputGlass
        border.color: root.checked ? Theme.e5BorderStrong : Theme.e5BorderSoft
        border.width: 1

        Rectangle {
            width: 22; height: 22
            radius: 11
            color: root.checked ? Theme.e5Star : Theme.textSecondary
            anchors.verticalCenter: parent.verticalCenter
            x: root.checked ? parent.width - width - 3 : 3
            Behavior on x { NumberAnimation { duration: Theme.animFast } }
            Behavior on color { ColorAnimation { duration: Theme.animFast } }
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: root.checked = !root.checked
        }
    }
}
