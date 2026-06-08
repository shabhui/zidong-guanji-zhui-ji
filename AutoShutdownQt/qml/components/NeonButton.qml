import QtQuick
import QtQuick.Controls
import ".."

Button {
    id: root

    property string variant: "secondary"
    property bool compact: false

    clip: true
    hoverEnabled: true
    implicitWidth: Math.max(compact ? 84 : 128, label.implicitWidth + (compact ? 30 : 38))
    implicitHeight: compact ? 36 : 44
    leftPadding: compact ? 12 : 18
    rightPadding: compact ? 12 : 18
    topPadding: 0
    bottomPadding: 0

    contentItem: Text {
        id: label
        text: root.text
        color: !root.enabled ? Theme.textSecondary
              : root.variant === "primary" ? Theme.e5Star
              : root.variant === "danger" ? Theme.danger
              : Theme.textPrimary
        opacity: root.enabled ? 1.0 : 0.55
        font.pixelSize: root.compact ? 12 : 14
        font.weight: Font.Bold
        fontSizeMode: Text.HorizontalFit
        minimumPixelSize: 10
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        maximumLineCount: 1
        elide: Text.ElideRight
    }

    background: Rectangle {
        radius: root.compact ? Theme.radiusSm : Theme.radiusMd
        color: !root.enabled ? "#1AFFFFFF"
              : root.down ? Theme.cardGlassActive
              : root.hovered ? Theme.cardGlassHover
              : root.variant === "primary" ? "#664CC9FF"
              : root.variant === "danger" ? "#30FF5C8A"
              : root.variant === "ghost" ? "#16FFFFFF"
              : Theme.cardGlass
        border.color: !root.enabled ? Theme.e5BorderSoft
                    : root.variant === "primary" ? Theme.borderStrong
                    : root.variant === "danger" ? Theme.danger
                    : root.hovered ? Theme.e5BorderStrong
                    : Theme.e5BorderSoft
        border.width: root.variant === "primary" ? 2 : 1
        antialiasing: true

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: Math.max(8, parent.height * 0.34)
            radius: parent.radius
            color: "#28FFFFFF"
            opacity: root.enabled ? 0.22 : 0.10
        }
    }

    scale: root.enabled && root.hovered ? 1.018 : 1.0

    Behavior on scale { NumberAnimation { duration: Theme.animFast; easing.type: Easing.OutCubic } }
}
