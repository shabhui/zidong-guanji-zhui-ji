import QtQuick
import ".."

// Full-window anime city backdrop with restrained liquid-light motion.
Item {
    id: root
    anchors.fill: parent
    clip: true

    property bool active: true

    Rectangle {
        id: liquidBaseGradient
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#182028" }
            GradientStop { position: 0.46; color: "#13232C" }
            GradientStop { position: 1.0; color: "#10161C" }
        }
    }

    Image {
        id: liquidBackdropImage
        x: -parent.width * 0.04
        y: -parent.height * 0.06
        width: parent.width * 1.08
        height: parent.height * 1.12
        source: "../assets/anime-skyline-bg.png"
        fillMode: Image.PreserveAspectCrop
        smooth: true
        mipmap: true
        opacity: 0.54
        scale: 1.03
        SequentialAnimation on x {
            id: liquidBackdropDriftAnimation
            running: root.active
            loops: Animation.Infinite
            NumberAnimation { from: -root.width * 0.04; to: 0; duration: 19000; easing.type: Easing.InOutSine }
            NumberAnimation { from: 0; to: -root.width * 0.04; duration: 19000; easing.type: Easing.InOutSine }
        }
        SequentialAnimation on scale {
            running: root.active
            loops: Animation.Infinite
            NumberAnimation { from: 1.03; to: 1.055; duration: 15000; easing.type: Easing.InOutSine }
            NumberAnimation { from: 1.055; to: 1.03; duration: 15000; easing.type: Easing.InOutSine }
        }
    }

    Rectangle {
        id: liquidAtmosphereWash
        anchors.fill: parent
        opacity: 0.46
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#38131B28" }
            GradientStop { position: 0.42; color: "#0AFFF4E8" }
            GradientStop { position: 0.72; color: "#24F7A7B9" }
            GradientStop { position: 1.0; color: "#183B7788" }
        }
    }

    Rectangle {
        id: liquidAuroraBandA
        x: -parent.width * 0.06
        y: parent.height * 0.19
        width: parent.width * 1.12
        height: 46
        radius: 23
        rotation: -5
        opacity: 0.11
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#00FFF2E6" }
            GradientStop { position: 0.28; color: "#4ADDE9E8" }
            GradientStop { position: 0.66; color: "#58FFB0C4" }
            GradientStop { position: 1.0; color: "#00F8D490" }
        }
        SequentialAnimation on x {
            running: root.active
            loops: Animation.Infinite
            NumberAnimation { from: -root.width * 0.06; to: -root.width * 0.01; duration: 11000; easing.type: Easing.InOutSine }
            NumberAnimation { from: -root.width * 0.01; to: -root.width * 0.06; duration: 11000; easing.type: Easing.InOutSine }
        }
    }

    Rectangle {
        id: liquidAuroraBandB
        x: -parent.width * 0.08
        y: parent.height * 0.69
        width: parent.width * 1.16
        height: 38
        radius: 19
        rotation: 4
        opacity: 0.10
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#00F8D490" }
            GradientStop { position: 0.36; color: "#4DFFB0C4" }
            GradientStop { position: 0.70; color: "#4ADDE9E8" }
            GradientStop { position: 1.0; color: "#00FFF2E6" }
        }
        SequentialAnimation on x {
            running: root.active
            loops: Animation.Infinite
            NumberAnimation { from: -root.width * 0.08; to: -root.width * 0.02; duration: 14000; easing.type: Easing.InOutSine }
            NumberAnimation { from: -root.width * 0.02; to: -root.width * 0.08; duration: 14000; easing.type: Easing.InOutSine }
        }
    }

    Item {
        id: liquidSparkleField
        anchors.fill: parent
        Repeater {
            model: 10
            Rectangle {
                required property int index
                width: 2 + (index % 3)
                height: width
                radius: width / 2
                x: ((index * 73) % 100) / 100 * liquidSparkleField.width
                y: ((index * 41) % 72) / 100 * liquidSparkleField.height
                color: index % 3 === 0 ? Theme.animeSakura : (index % 3 === 1 ? Theme.animeCyanGlow : Theme.animeVioletGlow)
                opacity: 0.12 + (index % 4) * 0.04
                SequentialAnimation on opacity {
                    running: root.active
                    loops: Animation.Infinite
                    NumberAnimation { to: 0.62; duration: 1300 + index * 55; easing.type: Easing.InOutSine }
                    NumberAnimation { to: 0.08; duration: 1500 + index * 45; easing.type: Easing.InOutSine }
                }
                SequentialAnimation on y {
                    running: root.active
                    loops: Animation.Infinite
                    NumberAnimation {
                        from: ((index * 41) % 72) / 100 * root.height
                        to: (((index * 41) % 72) / 100 * root.height) - 18
                        duration: 6200 + index * 150
                        easing.type: Easing.InOutSine
                    }
                    NumberAnimation {
                        to: ((index * 41) % 72) / 100 * root.height
                        duration: 6200 + index * 150
                        easing.type: Easing.InOutSine
                    }
                }
            }
        }
    }

    Rectangle {
    Rectangle {
        id: liquidHeroFocus
        anchors.left: parent.left
        anchors.top: parent.top
        width: Math.min(parent.width * 0.62, 760)
        height: parent.height
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#2E0A1018" }
            GradientStop { position: 0.72; color: "#120A1018" }
            GradientStop { position: 1.0; color: "#000A1018" }
        }
    }

    Rectangle {
        id: liquidSakuraLightStream
        anchors.left: parent.left
        y: parent.height * 0.16
        width: parent.width * 0.68
        height: 2
        radius: 1
        opacity: 0.46
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#00FFB0C4" }
            GradientStop { position: 0.36; color: "#9CFFB0C4" }
            GradientStop { position: 0.78; color: "#48DDE9E8" }
            GradientStop { position: 1.0; color: "#00DDE9E8" }
        }
        SequentialAnimation on opacity {
            running: root.active
            loops: Animation.Infinite
            NumberAnimation { from: 0.26; to: 0.58; duration: 3600; easing.type: Easing.InOutSine }
            NumberAnimation { from: 0.58; to: 0.26; duration: 3600; easing.type: Easing.InOutSine }
        }
    }

    Rectangle {
        id: liquidGlassFog
        anchors.fill: parent
        gradient: Gradient {
            orientation: Gradient.Vertical
            GradientStop { position: 0.0; color: "#16070D12" }
            GradientStop { position: 0.52; color: "#00070D12" }
            GradientStop { position: 1.0; color: "#4A070D12" }
        }
    }
        id: liquidReadabilityVeil
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#3A07091A" }
            GradientStop { position: 0.44; color: "#12070A18" }
            GradientStop { position: 1.0; color: "#76060916" }
        }
    }
}
