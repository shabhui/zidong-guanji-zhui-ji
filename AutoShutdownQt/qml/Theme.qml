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
    readonly property color accent: "#7DFFC4"
    readonly property color success: "#7DFFC4"
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

    readonly property color blogBgA: "#060814"
    readonly property color blogBgB: "#101827"
    readonly property color blogBgC: "#1A2030"
    readonly property color blogNavPanel: "#E0162132"
    readonly property color blogRail: "#C9141B29"
    readonly property color blogShell: "#A80B1020"
    readonly property color blogGlassPanel: "#801D2D48"
    readonly property color blogLyricPanel: "#E8061025"
    readonly property color blogCardBorder: "#66FFFFFF"
    readonly property color blogImageScrim: "#70000000"
    readonly property color blogAvatarRingA: "#7C5CFF"
    readonly property color blogAvatarRingB: "#FF62C7"
    readonly property color animeSakura: "#FF9BD7"
    readonly property color animeCyanGlow: "#67D8EF"
    readonly property color animeVioletGlow: "#9B7CFF"

    readonly property color heroPanel: "#223044"
    readonly property color commandBorder: "#86DFFF"
    readonly property color commandWarm: "#FFB86B"
    readonly property color commandCool: "#67D8EF"
    readonly property color commandRose: "#FF7A9B"
    readonly property color commandEmerald: "#7DFFC4"

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
