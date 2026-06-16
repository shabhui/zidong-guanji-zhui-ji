pragma Singleton
import QtQuick

QtObject {
    readonly property color bgDeep: "#090D14"
    readonly property color bgNight: "#111827"
    readonly property color bgViolet: "#171D2A"
    readonly property color bgPanel: bgNight

    readonly property color glassBase: "#24FFFFFF"
    readonly property color glassSoft: "#16FFFFFF"
    readonly property color glassStrong: "#32FFFFFF"
    readonly property color glassHover: "#3BFFFFFF"
    readonly property color surfaceGlass: glassBase
    readonly property color surfaceStrong: glassStrong
    readonly property color surfaceHover: glassHover

    readonly property color borderSoft: "#2CBDEBFF"
    readonly property color borderStrong: "#72CDEEFF"

    readonly property color primary: "#70C8EA"
    readonly property color accent: "#7EE1BA"
    readonly property color success: "#7EE1BA"
    readonly property color warning: "#FFD166"
    readonly property color danger: "#FF5C8A"

    readonly property color textPrimary: "#F7FAFF"
    readonly property color textSecondary: "#B9C5D6"

    readonly property color e5BgA: "#080B12"
    readonly property color e5BgB: "#101827"
    readonly property color e5BgC: "#151B2A"
    readonly property color e5Blue: "#5BBBD8"
    readonly property color e5Star: "#F7F2FF"

    readonly property color shellGlass: "#D0111722"
    readonly property color cardGlass: "#E0182130"
    readonly property color cardGlassHover: "#F01F2939"
    readonly property color cardGlassActive: "#F0263348"
    readonly property color dialogPanel: "#171D29"
    readonly property color dialogPanelRaised: "#1E2635"
    readonly property color dialogScrim: "#CC050716"
    readonly property color inputGlass: "#2AFFFFFF"
    readonly property color selectedOverlay: "#184CC9FF"
    readonly property color checkedTrack: "#284CC9FF"

    readonly property color e5BorderSoft: "#34BDEBFF"
    readonly property color e5BorderStrong: "#7E86DFFF"
    readonly property color e5BorderBlue: "#7486DFFF"

    readonly property real radiusSm: 8
    readonly property real radiusMd: 12
    readonly property real radiusLg: 14
    readonly property real radiusXl: 18

    readonly property real spaceXs: 4
    readonly property real spaceSm: 8
    readonly property real spaceMd: 16
    readonly property real spaceLg: 24
    readonly property real spaceXl: 32

    readonly property int animFast: 160
    readonly property int animNormal: 260
    readonly property int animSlow: 420
}
