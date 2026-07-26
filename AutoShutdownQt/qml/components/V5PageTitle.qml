import QtQuick
import QtQuick.Layouts
import ".."

Item {
    id: root

    property string eyebrow: "WORKSPACE"
    property string title: ""
    property string subtitle: ""
    property string statusText: ""
    property color statusColor: Theme.workspaceCyan

    implicitHeight: 66

    RowLayout {
        anchors.fill: parent
        spacing: 14

        Rectangle {
            Layout.preferredWidth: 3
            Layout.preferredHeight: 46
            color: root.statusColor
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 1

            Text {
                text: root.eyebrow
                color: Theme.workspaceCyan
                font.pixelSize: 9
                font.weight: Font.Bold
                font.letterSpacing: 2
            }

            Text {
                Layout.fillWidth: true
                text: root.title
                color: Theme.workspaceInk
                font.pixelSize: 24
                font.weight: Font.Bold
                elide: Text.ElideRight
            }

            Text {
                Layout.fillWidth: true
                text: root.subtitle
                color: Theme.workspaceMuted
                font.pixelSize: 10
                elide: Text.ElideRight
            }
        }

        V5StatusPill {
            visible: root.statusText !== ""
            text: root.statusText
            accentColor: root.statusColor
            Layout.alignment: Qt.AlignVCenter
        }
    }
}
