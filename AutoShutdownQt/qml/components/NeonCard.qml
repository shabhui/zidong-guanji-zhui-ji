import QtQuick
import ".."

Rectangle {
    id: root

    property color cardBorderColor: Theme.e5BorderSoft
    property color cardColor: Theme.cardGlass
    property color hoverColor: Theme.cardGlassHover
    property bool hoverable: true
    property bool active: false
    property color activeBorderColor: Theme.borderStrong

    color: active ? Theme.cardGlassActive : (hoverHandler.hovered && hoverable ? hoverColor : cardColor)
    radius: Theme.radiusLg
    border.color: active ? activeBorderColor : (hoverHandler.hovered && hoverable ? Theme.e5BorderStrong : cardBorderColor)
    border.width: 1
    antialiasing: true
    scale: hoverHandler.hovered && hoverable ? 1.004 : 1.0

    // Soft top highlight, kept restrained so solid panels stay readable.
    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: Math.max(22, parent.height * 0.18)
        radius: parent.radius
        color: "#20FFFFFF"
        opacity: 0.18
    }

    HoverHandler {
        id: hoverHandler
    }

    Behavior on color { ColorAnimation { duration: Theme.animNormal } }
    Behavior on border.color { ColorAnimation { duration: Theme.animNormal } }
    Behavior on scale { NumberAnimation { duration: Theme.animFast; easing.type: Easing.OutCubic } }
}
