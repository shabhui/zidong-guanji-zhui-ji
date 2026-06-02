import QtQuick
import QtQuick.Layouts
import ".."

Item {
    id: root

    property string title: "星空守夜中"
    property string subtitle: "Sleep safely under the stars"
    property color accentColor: Theme.e5Pink

    implicitWidth: 286
    implicitHeight: 520

    Rectangle {
        anchors.fill: parent
        radius: Theme.radiusXl
        color: Theme.cardGlass
        border.color: Theme.e5BorderPurple
        border.width: 1
        opacity: 0.96
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: 1
        radius: Theme.radiusXl - 1
        gradient: Gradient {
            orientation: Gradient.Vertical
            GradientStop { position: 0.0; color: "#35FFFFFF" }
            GradientStop { position: 0.38; color: "#10101834" }
            GradientStop { position: 1.0; color: "#301A1044" }
        }
    }

    Rectangle {
        id: halo
        width: parent.width * 0.72
        height: width
        radius: width / 2
        anchors.horizontalCenter: parent.horizontalCenter
        y: 58
        color: Theme.glowPink
        opacity: 0.28
        scale: 1.0
        SequentialAnimation on scale {
            loops: Animation.Infinite
            NumberAnimation { from: 0.96; to: 1.04; duration: Theme.floatVerySlow; easing.type: Easing.InOutSine }
            NumberAnimation { from: 1.04; to: 0.96; duration: Theme.floatVerySlow; easing.type: Easing.InOutSine }
        }
    }

    Rectangle {
        width: parent.width * 0.48
        height: width
        radius: width / 2
        anchors.horizontalCenter: parent.horizontalCenter
        y: 92
        color: Theme.glowBlue
        opacity: 0.30
    }

    Rectangle {
        id: head
        width: 96
        height: 118
        radius: 48
        anchors.horizontalCenter: parent.horizontalCenter
        y: 128
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#90F7F2FF" }
            GradientStop { position: 0.48; color: "#88FF6FD8" }
            GradientStop { position: 1.0; color: "#559B5CFF" }
        }
        border.color: Theme.e5BorderPink
        border.width: 1
    }

    Rectangle {
        id: hairLeft
        width: 74
        height: 190
        radius: 36
        x: parent.width / 2 - 104
        y: 142
        rotation: -18
        color: "#669B5CFF"
        border.color: "#88FF6FD8"
        border.width: 1
    }

    Rectangle {
        id: hairRight
        width: 74
        height: 190
        radius: 36
        x: parent.width / 2 + 30
        y: 142
        rotation: 18
        color: "#664CC9FF"
        border.color: "#88FF6FD8"
        border.width: 1
    }

    Rectangle {
        id: shoulders
        width: parent.width * 0.68
        height: 126
        radius: 52
        anchors.horizontalCenter: parent.horizontalCenter
        y: 284
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#309B5CFF" }
            GradientStop { position: 0.5; color: "#66FF6FD8" }
            GradientStop { position: 1.0; color: "#304CC9FF" }
        }
        border.color: Theme.e5BorderPink
        border.width: 1
    }

    Repeater {
        model: 18
        Rectangle {
            width: index % 4 === 0 ? 4 : 3
            height: width
            radius: width / 2
            x: 24 + ((index * 37) % Math.max(1, root.width - 52))
            y: 28 + ((index * 53) % Math.max(1, root.height - 130))
            color: index % 3 === 0 ? Theme.e5Pink : (index % 3 === 1 ? Theme.e5Blue : Theme.e5Star)
            opacity: 0.30
            SequentialAnimation on opacity {
                loops: Animation.Infinite
                PauseAnimation { duration: index * 70 }
                NumberAnimation { from: 0.16; to: 0.72; duration: Theme.twinkleSlow + index * 18; easing.type: Easing.InOutSine }
                NumberAnimation { from: 0.72; to: 0.16; duration: Theme.twinkleSlow + index * 14; easing.type: Easing.InOutSine }
            }
        }
    }

    ColumnLayout {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 24
        spacing: 6

        Text {
            Layout.fillWidth: true
            text: root.title
            color: Theme.textPrimary
            font.pixelSize: 22
            font.weight: Font.Bold
            horizontalAlignment: Text.AlignHCenter
        }

        Text {
            Layout.fillWidth: true
            text: root.subtitle
            color: Theme.textSecondary
            font.pixelSize: 12
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
        }
    }
}
