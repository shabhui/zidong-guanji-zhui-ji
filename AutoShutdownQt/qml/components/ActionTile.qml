import QtQuick
import QtQuick.Layouts
import ".."

Rectangle {
    id: root

    implicitHeight: 80
    radius: 0
    color: root.isSelected ? "#E0133044" : "#C90D192B"
    border.color: root.isSelected ? Theme.workspaceCyan : Theme.workspaceBorder
    border.width: 1

    property string actionKey: ""
    property string actionLabel: ""
    property string actionSub: ""
    property string actionGlyph: ""
    property bool light: false
    property bool isSelected: controller.selectedAction === actionKey
    readonly property string actionIndex: actionKey === "shutdown" ? "01"
                                          : actionKey === "sleep" ? "02"
                                          : actionKey === "hibernate" ? "03"
                                          : actionKey === "restart" ? "04"
                                          : actionKey === "logoff" ? "05"
                                          : actionKey === "lock" ? "06" : "--"

    enabled: !controller.powerActionInProgress
    scale: enabled && mouseArea.pressed ? 0.985 : 1.0
    opacity: enabled ? 1.0 : 0.52

    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 3
        color: root.isSelected ? Theme.workspaceCyan : "transparent"
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 14
        anchors.rightMargin: 10
        anchors.topMargin: 10
        anchors.bottomMargin: 9
        spacing: 3

        Text {
            text: root.actionIndex
            color: root.isSelected ? Theme.workspaceCyan : Theme.workspaceMuted
            font.pixelSize: 9
        }

        Item { Layout.fillHeight: true }

        Text {
            Layout.fillWidth: true
            Layout.maximumWidth: root.width - 66
            text: root.actionLabel
            color: Theme.workspaceInk
            font.pixelSize: 14
            font.weight: Font.Bold
            fontSizeMode: Text.HorizontalFit
            minimumPixelSize: 10
            maximumLineCount: 1
            elide: Text.ElideRight
        }

        Text {
            Layout.fillWidth: true
            Layout.maximumWidth: root.width - 66
            text: root.actionSub
            color: root.isSelected ? Theme.workspaceCyan : Theme.workspaceMuted
            font.pixelSize: 9
            fontSizeMode: Text.HorizontalFit
            minimumPixelSize: 8
            maximumLineCount: 1
            elide: Text.ElideRight
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        enabled: root.enabled
        hoverEnabled: true
        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ForbiddenCursor
        onClicked: controller.selectedAction = root.actionKey
    }

    Behavior on color { ColorAnimation { duration: Theme.motionFast } }
    Behavior on border.color { ColorAnimation { duration: Theme.motionFast } }
    Behavior on scale { NumberAnimation { duration: Theme.motionFast } }
}
