import QtQuick
import QtQuick.Layouts
import ".."

Rectangle {
    id: root

    default property alias contentData: contentColumn.data
    property string title: ""
    property string subtitle: ""
    property color accentColor: Theme.workspaceCyan
    property bool showAccent: true
    property int contentSpacing: 10

    implicitHeight: contentColumn.implicitHeight + (title === "" ? 30 : 66)
    radius: Theme.panelRadius
    color: Theme.workspaceSurface
    border.color: Theme.workspaceBorder
    border.width: 1

    Rectangle {
        visible: root.showAccent
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 2
        color: root.accentColor
        opacity: 0.88
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.rightMargin: 14
        anchors.topMargin: 14
        anchors.bottomMargin: 14
        spacing: root.contentSpacing

        ColumnLayout {
            visible: root.title !== ""
            Layout.fillWidth: true
            spacing: 2

            Text {
                Layout.fillWidth: true
                text: root.title
                color: Theme.workspaceInk
                font.pixelSize: 15
                font.weight: Font.Bold
                elide: Text.ElideRight
            }

            Text {
                visible: root.subtitle !== ""
                Layout.fillWidth: true
                text: root.subtitle
                color: Theme.workspaceMuted
                font.pixelSize: 10
                elide: Text.ElideRight
            }
        }

        ColumnLayout {
            id: contentColumn
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: root.contentSpacing
        }
    }
}
