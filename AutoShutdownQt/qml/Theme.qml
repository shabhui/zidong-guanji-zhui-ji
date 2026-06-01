pragma Singleton
import QtQuick

QtObject {
    // Background
    readonly property color bgDeep: "#090D1F"
    readonly property color bgPanel: "#172033"
    readonly property color surfaceGlass: "#26FFFFFF"
    readonly property color surfaceStrong: "#38FFFFFF"
    readonly property color surfaceHover: "#44FFFFFF"

    // Borders
    readonly property color borderSoft: "#33DDF7FF"
    readonly property color borderStrong: "#88DDF7FF"

    // Accent
    readonly property color primary: "#79D8FF"
    readonly property color secondary: "#B779FF"
    readonly property color accent: "#FF8ACF"
    readonly property color success: "#7DFFC4"
    readonly property color warning: "#FFD166"
    readonly property color danger: "#FF5C8A"

    // Text
    readonly property color textPrimary: "#FFF7FF"
    readonly property color textSecondary: "#CDBFEA"

    // Radii
    readonly property real radiusSm: 8
    readonly property real radiusMd: 14
    readonly property real radiusLg: 20
    readonly property real radiusXl: 26

    // Spacing
    readonly property real spaceXs: 4
    readonly property real spaceSm: 8
    readonly property real spaceMd: 16
    readonly property real spaceLg: 24
    readonly property real spaceXl: 32

    // Animation ms
    readonly property int animFast: 120
    readonly property int animNormal: 220
    readonly property int animSlow: 340
}
