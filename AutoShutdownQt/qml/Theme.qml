pragma Singleton
import QtQuick

QtObject {
    readonly property color bgDeep: "#070A1A"
    readonly property color bgNight: "#101437"
    readonly property color bgViolet: "#25114A"
    readonly property color bgPanel: bgNight

    readonly property color glassBase: "#24FFFFFF"
    readonly property color glassSoft: "#18FFFFFF"
    readonly property color glassStrong: "#36FFFFFF"
    readonly property color glassHover: "#46FFFFFF"
    readonly property color surfaceGlass: glassBase
    readonly property color surfaceStrong: glassStrong
    readonly property color surfaceHover: glassHover

    readonly property color borderSoft: "#40BDEBFF"
    readonly property color borderStrong: "#9AE6FFFF"
    readonly property color borderPink: "#AAFF8ACF"

    readonly property color primary: "#79D8FF"
    readonly property color secondary: "#B779FF"
    readonly property color accent: "#FF8ACF"
    readonly property color success: "#7DFFC4"
    readonly property color warning: "#FFD166"
    readonly property color danger: "#FF5C8A"

    readonly property color textPrimary: "#FFF7FF"
    readonly property color textSecondary: "#D9CCF3"

    readonly property real radiusSm: 10
    readonly property real radiusMd: 16
    readonly property real radiusLg: 22
    readonly property real radiusXl: 30

    readonly property real spaceXs: 4
    readonly property real spaceSm: 8
    readonly property real spaceMd: 16
    readonly property real spaceLg: 24
    readonly property real spaceXl: 32

    readonly property int animFast: 130
    readonly property int animNormal: 240
    readonly property int animSlow: 420
    readonly property int floatSlow: 7600
}
