import QtQuick
import ".."

NeonCard {
    id: root
    width: 155
    height: 74

    property string actionKey: ""
    property string actionLabel: ""
    property string actionSub: ""
    property bool isSelected: controller.selectedAction === actionKey

    radius: Theme.radiusMd
    cardColor: isSelected ? "#44FFFFFF" : Theme.surfaceGlass
    cardBorderColor: isSelected ? Theme.accent : Theme.borderSoft

    scale: mouseArea.containsMouse ? 1.03 : 1.0
    Behavior on scale { NumberAnimation { duration: Theme.animFast } }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        hoverEnabled: true
        onClicked: controller.selectedAction = root.actionKey
    }

    Column {
        anchors.centerIn: parent
        spacing: 4
        Text {
            text: actionLabel
            color: root.isSelected ? Theme.textPrimary : Theme.textSecondary
            font.pixelSize: 15
            font.weight: Font.Bold
            anchors.horizontalCenter: parent.horizontalCenter
        }
        Text {
            text: actionSub
            color: Theme.textSecondary
            font.pixelSize: 10
            anchors.horizontalCenter: parent.horizontalCenter
            opacity: root.isSelected ? 1 : 0.6
        }
    }
}
