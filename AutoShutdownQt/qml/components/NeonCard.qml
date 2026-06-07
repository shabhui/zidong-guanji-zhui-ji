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

    color: active ? Theme.cardGlassActive : (hoverHandler.hovered && hoverable ? hoverColor : cardColor)
    radius: Theme.radiusLg
    border.color: active ? activeBorderColor : (hoverHandler.hovered && hoverable ? Theme.e5BorderStrong : cardBorderColor)
    border.width: active ? 2 : 1
    antialiasing: true
    scale: hoverHandler.hovered && hoverable ? 1.008 : 1.0

    // Soft top highlight, kept restrained so solid panels stay readable.
    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: Math.max(26, parent.height * 0.24)
        radius: parent.radius
        color: "#26FFFFFF"
        opacity: 0.28
    }

    // Corner glows are deliberately quiet to avoid visual bleed-through.
    Rectangle {
        width: Math.min(parent.width * 0.45, 140)
        height: width
        radius: width / 2
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.rightMargin: -width * 0.32
        anchors.topMargin: -width * 0.38
        color: Theme.e5Blue
        opacity: hoverHandler.hovered && hoverable ? 0.10 : 0.035
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
        opacity: hoverHandler.hovered && hoverable ? 0.08 : 0.025
    }

    HoverHandler {
        id: hoverHandler
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
