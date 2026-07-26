import QtQuick
import ".."

Rectangle {
    id: root

    property color cardBorderColor: Theme.workspaceBorder
    property color cardColor: Theme.workspaceSurface
    property color hoverColor: Theme.workspaceSurfaceRaised
    property bool hoverable: true
    property bool active: false
    property color activeBorderColor: Theme.workspaceAccent
    property bool liquid: false

    color: active ? Theme.controlSurfaceSelected : (hoverHandler.hovered && hoverable ? hoverColor : cardColor)
    radius: Theme.panelRadius
    border.color: active ? activeBorderColor : (hoverHandler.hovered && hoverable ? Theme.workspaceBorderStrong : cardBorderColor)
    border.width: 1
    antialiasing: true
    clip: true

    Rectangle {
        visible: root.liquid
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: Math.max(24, parent.height * 0.22)
        radius: parent.radius
        gradient: Gradient {
            GradientStop { position: 0.0; color: Theme.liquidHighlight }
            GradientStop { position: 0.55; color: Theme.liquidSheen }
            GradientStop { position: 1.0; color: "#00FFFFFF" }
        }
    }

    HoverHandler {
        id: hoverHandler
    }

    Behavior on color { ColorAnimation { duration: Theme.motionNormal; easing.type: Easing.OutCubic } }
    Behavior on border.color { ColorAnimation { duration: Theme.motionNormal; easing.type: Easing.OutCubic } }
}
