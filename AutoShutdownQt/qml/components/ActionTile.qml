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

    active: isSelected
    cardColor: isSelected ? Theme.cardGlassActive : Theme.cardGlass
    hoverColor: isSelected ? "#66301F78" : Theme.cardGlassHover
    cardBorderColor: isSelected ? Theme.e5BorderPink : Theme.e5BorderSoft
    activeBorderColor: Theme.e5BorderPink
    scale: mouseArea.containsMouse ? 1.025 : 1.0

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
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: controller.selectedAction = root.actionKey
    }

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 4
        Text {
            text: actionLabel
            color: root.isSelected ? Theme.textPrimary : Theme.textSecondary
            font.pixelSize: 16
            font.weight: Font.Bold
            Layout.alignment: Qt.AlignHCenter
        }
        Text {
            text: actionSub
            color: root.isSelected ? Theme.primary : Theme.textSecondary
            font.pixelSize: 10
            opacity: root.isSelected ? 1 : 0.72
            Layout.alignment: Qt.AlignHCenter
        }
    }

    Behavior on scale { NumberAnimation { duration: Theme.animFast; easing.type: Easing.OutCubic } }
}
