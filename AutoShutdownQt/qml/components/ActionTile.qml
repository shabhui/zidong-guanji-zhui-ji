import QtQuick
import QtQuick.Layouts
import ".."

NeonCard {
    id: root
    implicitHeight: 78
    hoverable: true

    property string actionKey: ""
    property string actionLabel: ""
    property string actionSub: ""
    property bool isSelected: controller.selectedAction === actionKey

    enabled: !controller.powerActionInProgress
    active: isSelected
    cardColor: isSelected ? Theme.cardGlassActive : Theme.cardGlass
    hoverColor: isSelected ? "#66301F78" : Theme.cardGlassHover
    cardBorderColor: isSelected ? Theme.e5BorderPink : Theme.e5BorderSoft
    activeBorderColor: Theme.e5BorderPink
    scale: enabled && mouseArea.containsMouse ? 1.025 : 1.0
    opacity: enabled ? 1.0 : 0.56

    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 4
        radius: 2
        color: root.isSelected ? Theme.e5Pink : "transparent"
        opacity: root.isSelected ? 1 : 0
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: 1
        radius: parent.radius - 1
        color: root.isSelected ? Theme.glowBlue : "transparent"
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        enabled: root.enabled
        hoverEnabled: true
        cursorShape: mouseArea.enabled ? Qt.PointingHandCursor : Qt.ForbiddenCursor
        onClicked: controller.selectedAction = root.actionKey
    }

    ColumnLayout {
        anchors.centerIn: parent
        width: parent.width - 18
        spacing: 4
        Text {
            text: actionLabel
            color: root.isSelected ? Theme.textPrimary : Theme.textSecondary
            font.pixelSize: 16
            font.weight: Font.Bold
            fontSizeMode: Text.HorizontalFit
            minimumPixelSize: 11
            maximumLineCount: 1
            elide: Text.ElideRight
            horizontalAlignment: Text.AlignHCenter
            Layout.alignment: Qt.AlignHCenter
            Layout.maximumWidth: parent.width
        }
        Text {
            text: actionSub
            color: root.isSelected ? Theme.primary : Theme.textSecondary
            font.pixelSize: 10
            fontSizeMode: Text.HorizontalFit
            minimumPixelSize: 8
            maximumLineCount: 1
            elide: Text.ElideRight
            horizontalAlignment: Text.AlignHCenter
            opacity: root.isSelected ? 1 : 0.72
            Layout.alignment: Qt.AlignHCenter
            Layout.maximumWidth: parent.width
        }
    }

    Behavior on scale { NumberAnimation { duration: Theme.animFast; easing.type: Easing.OutCubic } }
}
