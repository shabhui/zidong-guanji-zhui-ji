pragma Singleton
import QtQuick

QtObject {
    readonly property color bgDeep: "#070B12"
    readonly property color bgNight: "#101826"
    readonly property color bgViolet: "#151B2A"
    readonly property color bgPanel: bgNight

    readonly property color glassBase: "#2EFFFFFF"
    readonly property color glassSoft: "#1FFFFFFF"
    readonly property color glassStrong: "#3DFFFFFF"
    readonly property color glassHover: "#4AFFFFFF"
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

    readonly property color e5BgA: "#080B12"
    readonly property color e5BgB: "#101827"
    readonly property color e5BgC: "#151B2A"
    readonly property color e5Pink: "#FF7AB6"
    readonly property color e5Purple: "#8E7CFF"
    readonly property color e5Blue: "#58C7E8"
    readonly property color e5Star: "#F7F2FF"

    readonly property color shellGlass: "#D0101624"
    readonly property color cardGlass: "#E0182232"
    readonly property color cardGlassHover: "#F0202B3D"
    readonly property color cardGlassActive: "#F02A3350"
    readonly property color dialogPanel: "#181D2A"
    readonly property color dialogPanelRaised: "#20283A"
    readonly property color dialogScrim: "#CC050716"
    readonly property color inputGlass: "#2AFFFFFF"

    readonly property color e5BorderSoft: "#55BDEBFF"
    readonly property color e5BorderStrong: "#B44CC9FF"
    readonly property color e5BorderPink: "#BBFF6FD8"
    readonly property color e5BorderPurple: "#AA9B5CFF"
    readonly property color e5BorderBlue: "#AA4CC9FF"

    readonly property color glowBlue: "#2458C7E8"
    readonly property color glowPink: "#24FF7AB6"
    readonly property color glowPurple: "#228E7CFF"

    readonly property int floatVerySlow: 11200
    readonly property int twinkleSlow: 1800

    readonly property real radiusSm: 6
    readonly property real radiusMd: 8
    readonly property real radiusLg: 8
    readonly property real radiusXl: 10

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
