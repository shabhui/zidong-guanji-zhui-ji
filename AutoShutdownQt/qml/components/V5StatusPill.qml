import QtQuick
import QtQuick.Layouts
import ".."

Rectangle {
    id: root

    property string text: ""
    property color accentColor: Theme.workspaceCyan

    implicitWidth: statusRow.implicitWidth + 18
    implicitHeight: 28
    radius: Theme.controlRadius
    color: "#14000000"
    border.color: Qt.rgba(accentColor.r, accentColor.g, accentColor.b, 0.32)
    border.width: 1

    RowLayout {
        id: statusRow
        anchors.centerIn: parent
        spacing: 7

        Rectangle {
            Layout.preferredWidth: 7
            Layout.preferredHeight: 7
            radius: 3.5
            color: root.accentColor
        }

        Text {
            text: root.text
            color: root.accentColor
            font.pixelSize: 10
            font.weight: Font.DemiBold
        }
    }
}
