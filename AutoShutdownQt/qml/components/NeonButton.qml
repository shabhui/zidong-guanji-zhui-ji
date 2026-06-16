import QtQuick
import QtQuick.Controls
import ".."

Button {
    id: root

    property string variant: "secondary"
    property bool compact: false

    clip: true
    hoverEnabled: true
    implicitWidth: Math.max(compact ? 84 : 128, label.implicitWidth + (compact ? 30 : 40))
    implicitHeight: compact ? 36 : 46
    leftPadding: compact ? 12 : 18
    rightPadding: compact ? 12 : 18
    topPadding: 0
    bottomPadding: 0

    contentItem: Text {
        id: label
        text: root.text
        color: !root.enabled ? Theme.textSecondary
              : root.variant === "primary" ? Theme.e5Star
              : root.variant === "danger" ? "#FF7A9B"
              : root.variant === "quietDanger" ? "#FF8BA6"
              : Theme.textPrimary
        opacity: root.enabled ? 1.0 : 0.55
        font.pixelSize: root.compact ? 12 : 14
        font.weight: root.variant === "primary" ? Font.DemiBold : Font.Medium
        fontSizeMode: Text.HorizontalFit
        minimumPixelSize: 10
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        maximumLineCount: 1
        elide: Text.ElideRight
    }

    background: Rectangle {
        radius: root.compact ? Theme.radiusMd : Theme.radiusLg
        color: !root.enabled ? "#1AFFFFFF"
              : root.down ? Theme.cardGlassActive
              : root.hovered ? Theme.cardGlassHover
              : root.variant === "primary" ? "#4D4CC9FF"
              : root.variant === "danger" ? "#24FF5C8A"
              : root.variant === "quietDanger" ? "#14FF5C8A"
              : root.variant === "ghost" ? "#10FFFFFF"
              : Theme.cardGlass
        border.color: !root.enabled ? Theme.e5BorderSoft
                    : root.variant === "primary" ? Theme.borderStrong
                    : root.variant === "danger" ? "#B8FF5C8A"
                    : root.variant === "quietDanger" ? "#70FF5C8A"
                    : root.hovered ? Theme.e5BorderStrong
                    : Theme.e5BorderSoft
        border.width: 1
        antialiasing: true

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: Math.max(8, parent.height * 0.34)
            radius: parent.radius
            color: "#22FFFFFF"
            opacity: root.enabled ? 0.22 : 0.10
        }
    }

    scale: root.enabled && root.hovered ? 1.006 : 1.0

    Behavior on scale { NumberAnimation { duration: Theme.animFast; easing.type: Easing.OutCubic } }
}
