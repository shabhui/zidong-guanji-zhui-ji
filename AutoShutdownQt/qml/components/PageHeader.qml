import QtQuick
import QtQuick.Layouts
import ".."

Item {
    id: root

    property string eyebrow: "工作台"
    property string title: ""
    property string description: ""
    property string statusText: ""
    property color statusColor: Theme.workspaceAccent

    implicitHeight: 70
    height: implicitHeight

    RowLayout {
        anchors.fill: parent
        spacing: 16

        Rectangle {
            Layout.preferredWidth: 4
            Layout.fillHeight: true
        radius: 2
        color: root.statusColor

        Behavior on color { ColorAnimation { duration: Theme.motionNormal; easing.type: Easing.OutCubic } }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            Text {
                text: root.eyebrow
                color: Theme.workspaceMuted
                font.pixelSize: 11
                font.weight: Font.DemiBold
            }

            Text {
                text: root.title
                color: Theme.workspaceInk
                font.pixelSize: 26
                font.weight: Font.Bold
                elide: Text.ElideRight
                Layout.fillWidth: true
            }

            Text {
                visible: root.description !== ""
                text: root.description
                color: Theme.workspaceMuted
                font.pixelSize: 12
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
        }

        Rectangle {
            visible: root.statusText !== ""
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: statusLabel.implicitWidth + 20
            implicitHeight: 28
            radius: 14
            color: Qt.rgba(root.statusColor.r, root.statusColor.g, root.statusColor.b, 0.12)
            border.color: Qt.rgba(root.statusColor.r, root.statusColor.g, root.statusColor.b, 0.32)
            border.width: 1

            Behavior on color { ColorAnimation { duration: Theme.motionNormal; easing.type: Easing.OutCubic } }
            Behavior on border.color { ColorAnimation { duration: Theme.motionNormal; easing.type: Easing.OutCubic } }

            Text {
                id: statusLabel
                anchors.centerIn: parent
                text: root.statusText
                color: root.statusColor
                font.pixelSize: 12
                font.weight: Font.DemiBold
            }
        }
    }
}
