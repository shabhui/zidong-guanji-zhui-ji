import QtQuick
import ".."

Rectangle {
    id: root

    property color cardBorderColor: Theme.e5BorderSoft
    property color cardColor: Theme.cardGlass
    property color hoverColor: Theme.cardGlassHover
    property bool hoverable: true
    property bool breathing: false
    property bool active: false
    property color activeBorderColor: Theme.e5BorderPink

    color: active ? Theme.cardGlassActive : (hoverArea.containsMouse && hoverable ? hoverColor : cardColor)
    radius: Theme.radiusLg
    border.color: active ? activeBorderColor : (hoverArea.containsMouse && hoverable ? Theme.e5BorderStrong : cardBorderColor)
    border.width: active ? 2 : 1
    antialiasing: true
    scale: hoverArea.containsMouse && hoverable ? 1.008 : 1.0

    // Soft glass highlight across the top edge.
    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: Math.max(26, parent.height * 0.24)
        radius: parent.radius
        color: "#26FFFFFF"
        opacity: 0.78
    }

    // Anime-style corner glow, subtle and clipped by the card bounds.
    Rectangle {
        width: Math.min(parent.width * 0.45, 140)
        height: width
        radius: width / 2
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.rightMargin: -width * 0.32
        anchors.topMargin: -width * 0.38
        color: Theme.e5Blue
        opacity: hoverArea.containsMouse && hoverable ? 0.18 : 0.09
    }

    Rectangle {
        width: Math.min(parent.width * 0.35, 110)
        height: width
        radius: width / 2
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.leftMargin: -width * 0.42
        anchors.bottomMargin: -width * 0.48
        color: Theme.e5Pink
        opacity: hoverArea.containsMouse && hoverable ? 0.12 : 0.055
    }

    MouseArea {
        id: hoverArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
    }

    SequentialAnimation on opacity {
        running: root.breathing
        loops: Animation.Infinite
        NumberAnimation { from: 0.94; to: 1.0; duration: Theme.animSlow; easing.type: Easing.InOutSine }
        NumberAnimation { from: 1.0; to: 0.94; duration: Theme.animSlow; easing.type: Easing.InOutSine }
    }

    Behavior on color { ColorAnimation { duration: Theme.animNormal } }
    Behavior on border.color { ColorAnimation { duration: Theme.animNormal } }
    Behavior on scale { NumberAnimation { duration: Theme.animFast; easing.type: Easing.OutCubic } }
}
