import QtQuick
import ".."

Item {
    id: root
    width: 185
    height: 46
    property string label: ""
    property bool active: false
    property string pageName: ""

    Rectangle {
        anchors.fill: parent
        radius: Theme.radiusMd
        color: root.active ? Theme.surfaceStrong : "transparent"
        border.color: root.active ? Theme.borderStrong : "transparent"
        border.width: 1

        Row {
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: Theme.spaceMd
            spacing: Theme.spaceSm

            Rectangle {
                width: 3; height: 22
                radius: 2
                color: root.active ? Theme.accent : "transparent"
                anchors.verticalCenter: parent.verticalCenter
            }

            Text {
                text: root.label
                color: root.active ? Theme.textPrimary : Theme.textSecondary
                font.pixelSize: 14
                font.weight: root.active ? Font.Bold : Font.Normal
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: root.parent.parent.pageStack.currentIndex = root.parent.parent.pageMap[root.pageName]
    }
}
