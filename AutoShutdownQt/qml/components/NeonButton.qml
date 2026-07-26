import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Button {
    id: root

    property string variant: "secondary"
    property bool compact: false
    property string leadingIcon: ""

    readonly property bool isPrimary: variant === "primary" || variant === "launch"
    readonly property bool isCyan: variant === "cyan"
    readonly property bool isDanger: variant === "danger" || variant === "quietDanger"
    readonly property bool isGhost: variant === "ghost"

    clip: true
    hoverEnabled: true
    implicitWidth: Math.max(compact ? 72 : 112, contentRow.implicitWidth + (compact ? 24 : 34))
    implicitHeight: compact ? 32 : 40
    leftPadding: compact ? 12 : 17
    rightPadding: compact ? 12 : 17
    topPadding: 0
    bottomPadding: 0

    contentItem: RowLayout {
        id: contentRow
        spacing: root.leadingIcon === "" ? 0 : 7

        Text {
            visible: root.leadingIcon !== ""
            text: root.leadingIcon
            color: label.color
            opacity: root.enabled ? 0.92 : 0.42
            font.pixelSize: root.compact ? 11 : 13
            font.weight: Font.Bold
            Layout.alignment: Qt.AlignVCenter
        }

        Text {
            id: label
            Layout.fillWidth: true
            text: root.text
            color: !root.enabled ? Theme.workspaceMuted
                  : root.isPrimary || root.isCyan ? Theme.workspaceBackground
                  : root.isDanger ? Theme.workspaceDanger
                  : Theme.workspaceInk
            opacity: root.enabled ? 1.0 : 0.5
            font.pixelSize: root.compact ? 11 : 13
            font.weight: root.isPrimary || root.isCyan ? Font.Bold : Font.DemiBold
            fontSizeMode: Text.HorizontalFit
            minimumPixelSize: 9
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            maximumLineCount: 1
            elide: Text.ElideRight
        }
    }

    background: Rectangle {
        radius: Theme.controlRadius
        color: !root.enabled ? Theme.workspaceSurfaceMuted
              : root.down && root.isCyan ? Qt.darker(Theme.workspaceCyan, 1.18)
              : root.down && root.isPrimary ? Qt.darker(Theme.workspaceAccent, 1.14)
              : root.hovered && root.isCyan ? Qt.lighter(Theme.workspaceCyan, 1.08)
              : root.hovered && root.isPrimary ? Theme.workspaceAccentHover
              : root.hovered && !root.isGhost ? Theme.controlSurfaceHover
              : root.isCyan ? Theme.workspaceCyan
              : root.isPrimary ? Theme.workspaceAccent
              : root.variant === "danger" ? "#28FF6B87"
              : root.variant === "quietDanger" ? "#10000000"
              : root.isGhost ? "transparent"
              : Theme.controlSurface
        border.color: !root.enabled ? Theme.workspaceBorder
                    : root.isCyan ? Theme.workspaceCyan
                    : root.isPrimary ? Theme.workspaceAccent
                    : root.isDanger ? "#88FF6B87"
                    : root.hovered ? Theme.controlBorderHover
                    : root.isGhost ? Theme.workspaceBorder
                    : Theme.controlBorder
        border.width: 1
        antialiasing: true

        Behavior on color { ColorAnimation { duration: Theme.motionFast } }
        Behavior on border.color { ColorAnimation { duration: Theme.motionFast } }
    }

    scale: root.enabled && root.down ? 0.985 : 1.0
    Behavior on scale { NumberAnimation { duration: Theme.motionFast; easing.type: Easing.OutCubic } }
}
