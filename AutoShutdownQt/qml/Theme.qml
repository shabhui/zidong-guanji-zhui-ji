pragma Singleton
import QtQuick

QtObject {
    readonly property color workspaceBackground: "#FF050B16"
    readonly property color workspaceTopbar: "#F2070D18"
    readonly property color workspaceSidebar: "#F20A1220"
    readonly property color workspaceSurface: "#E80B1526"
    readonly property color workspaceSurfaceRaised: "#F0101D31"
    readonly property color workspaceSurfaceMuted: "#FF17263D"
    readonly property color workspaceBorder: "#FF263A57"
    readonly property color workspaceBorderStrong: "#FF4B6C91"
    readonly property color workspaceInk: "#FFF4F7FC"
    readonly property color workspaceMuted: "#FF91A4BC"
    readonly property color workspaceAccent: "#FFFF6FAE"
    readonly property color workspaceAccentHover: "#FFFF89BE"
    readonly property color workspaceAccentSoft: "#35FF6FAE"
    readonly property color workspaceCyan: "#FF62E6FF"
    readonly property color workspaceCoral: "#FFFF6FAE"
    readonly property color workspaceSuccess: "#FF64F5D4"
    readonly property color workspaceWarning: "#FFFFC96B"
    readonly property color workspaceDanger: "#FFFF6B87"

    readonly property color controlSurface: "#CC0E1A2D"
    readonly property color controlSurfaceHover: "#F0162942"
    readonly property color controlSurfacePressed: "#FF1A314E"
    readonly property color controlSurfaceSelected: "#F0133044"
    readonly property color controlBorder: "#FF314761"
    readonly property color controlBorderHover: workspaceCyan
    readonly property color controlShadow: "#66000000"
    readonly property color animeAtmosphereSakura: workspaceAccent
    readonly property color animeAtmosphereCyan: workspaceCyan

    readonly property color bgDeep: workspaceBackground
    readonly property color bgNight: "#FF08101E"
    readonly property color bgViolet: "#FF12152A"
    readonly property color bgPanel: workspaceSurface

    readonly property color glassBase: workspaceSurface
    readonly property color glassSoft: workspaceSurfaceRaised
    readonly property color glassStrong: "#F0172438"
    readonly property color glassHover: controlSurfaceHover
    readonly property color surfaceGlass: workspaceSurface
    readonly property color surfaceStrong: workspaceSurfaceRaised
    readonly property color surfaceHover: controlSurfaceHover

    readonly property color borderSoft: workspaceBorder
    readonly property color borderStrong: workspaceCyan
    readonly property color liquidEdge: "#5062E6FF"
    readonly property color liquidHighlight: "#2862E6FF"
    readonly property color liquidSheen: "#12FFFFFF"
    readonly property color liquidGlowCyan: "#3062E6FF"
    readonly property color liquidGlowSakura: "#30FF6FAE"
    readonly property color liquidGlowViolet: "#304E67FF"

    readonly property color primary: workspaceAccent
    readonly property color accent: workspaceSuccess
    readonly property color success: workspaceSuccess
    readonly property color warning: workspaceWarning
    readonly property color danger: workspaceDanger

    readonly property color textPrimary: workspaceInk
    readonly property color textSecondary: workspaceMuted

    readonly property color e5BgA: workspaceBackground
    readonly property color e5BgB: workspaceSurfaceRaised
    readonly property color e5BgC: workspaceSurfaceMuted
    readonly property color e5Blue: workspaceCyan
    readonly property color e5Star: "#FFFFFFFF"

    readonly property color shellGlass: workspaceSurface
    readonly property color cardGlass: workspaceSurface
    readonly property color cardGlassHover: workspaceSurfaceRaised
    readonly property color cardGlassActive: controlSurfaceSelected
    readonly property color dialogPanel: "#FF0B1627"
    readonly property color dialogPanelRaised: "#FF122239"
    readonly property color dialogScrim: "#B8050B16"
    readonly property color inputGlass: "#E80D1A2C"
    readonly property color selectedOverlay: "#3062E6FF"
    readonly property color checkedTrack: "#5062E6FF"

    readonly property color blogBgA: workspaceBackground
    readonly property color blogBgB: workspaceSurfaceRaised
    readonly property color blogBgC: workspaceSurfaceMuted
    readonly property color blogNavPanel: workspaceTopbar
    readonly property color blogRail: workspaceSidebar
    readonly property color blogShell: workspaceSurface
    readonly property color blogGlassPanel: workspaceSurface
    readonly property color blogLyricPanel: workspaceSurfaceRaised
    readonly property color blogCardBorder: workspaceBorder
    readonly property color blogImageScrim: "#88050B16"
    readonly property color blogAvatarRingA: workspaceAccent
    readonly property color blogAvatarRingB: workspaceCyan
    readonly property color animeSakura: workspaceCoral
    readonly property color animeCyanGlow: workspaceCyan
    readonly property color animeVioletGlow: "#FF9A7CFF"

    readonly property color launchCanvas: workspaceBackground
    readonly property color launchSurface: workspaceSurface
    readonly property color launchSurfaceMuted: workspaceSurfaceRaised
    readonly property color launchBorder: workspaceBorder
    readonly property color launchText: workspaceInk
    readonly property color launchTextMuted: workspaceMuted
    readonly property color launchAccent: workspaceAccent
    readonly property color launchAccentHover: workspaceAccentHover
    readonly property color launchAccentSoft: workspaceAccentSoft
    readonly property color launchAccentText: workspaceBackground
    readonly property color launchSuccess: workspaceSuccess
    readonly property color launchPanel: workspaceSurface
    readonly property color launchPanelSoft: workspaceSurfaceRaised
    readonly property color launchPrimary: workspaceAccent
    readonly property color launchPrimaryHover: workspaceAccentHover
    readonly property color launchMint: workspaceCyan
    readonly property color launchInk: workspaceInk
    readonly property color launchSkyTop: "#FF08111F"
    readonly property color launchSkyBottom: "#FF120D1C"
    readonly property color launchMoon: "#FFFFF0BA"
    readonly property color launchStar: "#FFFFFFFF"
    readonly property color launchPetal: workspaceAccent

    readonly property color heroPanel: workspaceSurfaceRaised
    readonly property color commandBorder: workspaceBorderStrong
    readonly property color commandWarm: workspaceWarning
    readonly property color commandCool: workspaceCyan
    readonly property color commandRose: workspaceCoral
    readonly property color commandEmerald: workspaceSuccess

    readonly property color e5BorderSoft: workspaceBorder
    readonly property color e5BorderStrong: workspaceBorderStrong
    readonly property color e5BorderBlue: workspaceCyan

    readonly property real controlRadius: 2
    readonly property real panelRadius: 4
    readonly property real radiusSm: controlRadius
    readonly property real radiusMd: 4
    readonly property real radiusLg: 6
    readonly property real radiusXl: 10

    readonly property real spaceXs: 4
    readonly property real spaceSm: 8
    readonly property real spaceMd: 16
    readonly property real spaceLg: 24
    readonly property real spaceXl: 32

    readonly property int motionFast: 110
    readonly property int motionNormal: 190
    readonly property int motionSlow: 320

    readonly property int animFast: motionFast
    readonly property int animNormal: motionNormal
    readonly property int animSlow: motionSlow
}
