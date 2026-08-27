import QtQuick
import QtQuick.Layouts
import ".."

Rectangle {
    id: root

    property string iconText: ""
    property string label: ""
    property string detail: ""
    property bool selected: false
    signal clicked()

    implicitHeight: 54
    radius: Theme.controlRadius
    color: selected ? Theme.controlSurfaceSelected : (mouseArea.containsMouse ? Theme.controlSurfaceHover : "transparent")
    border.color: selected ? Theme.workspaceAccent : "transparent"
    border.width: 1

    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 3
        radius: 1.5
        color: root.selected ? Theme.workspaceAccent : "transparent"
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 12
        anchors.rightMargin: 10
        spacing: 10

        Rectangle {
            Layout.preferredWidth: 30
            Layout.preferredHeight: 30
            radius: Theme.controlRadius
            color: root.selected ? Theme.workspaceAccent : Theme.workspaceSurfaceMuted

            Text {
                anchors.centerIn: parent
                text: root.iconText
                color: root.selected ? Theme.e5Star : Theme.workspaceMuted
                font.pixelSize: 12
                font.weight: Font.Bold
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 0

            Text {
                Layout.fillWidth: true
                text: root.label
                color: Theme.workspaceInk
                font.pixelSize: 14
                font.weight: root.selected ? Font.DemiBold : Font.Medium
                elide: Text.ElideRight
            }

            Text {
                Layout.fillWidth: true
                text: root.detail
                color: Theme.workspaceMuted
                font.pixelSize: 10
                elide: Text.ElideRight
            }
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }

    Behavior on color { ColorAnimation { duration: Theme.motionFast } }
    Behavior on border.color { ColorAnimation { duration: Theme.motionFast } }
}
