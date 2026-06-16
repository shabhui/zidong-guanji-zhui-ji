import QtQuick
import QtQuick.Layouts
import ".."

NeonCard {
    id: root
    implicitHeight: 74
    hoverable: true

    property string actionKey: ""
    property string actionLabel: ""
    property string actionSub: ""
    property bool isSelected: controller.selectedAction === actionKey

    enabled: !controller.powerActionInProgress
    active: isSelected
    cardColor: isSelected ? Theme.cardGlassActive : Theme.cardGlass
    hoverColor: isSelected ? Theme.selectedOverlay : Theme.cardGlassHover
    cardBorderColor: isSelected ? Theme.borderStrong : Theme.e5BorderSoft
    activeBorderColor: Theme.borderStrong
    scale: enabled && mouseArea.containsMouse ? 1.006 : 1.0
    opacity: enabled ? 1.0 : 0.56

    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 3
        radius: 2
        color: root.isSelected ? Theme.primary : "transparent"
        opacity: root.isSelected ? 1 : 0
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: 1
        radius: parent.radius - 1
        color: root.isSelected ? Theme.selectedOverlay : "transparent"
        opacity: root.isSelected ? 0.72 : 0
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
            font.weight: Font.DemiBold
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
