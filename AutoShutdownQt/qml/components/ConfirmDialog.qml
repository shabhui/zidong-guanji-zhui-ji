import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "."

Dialog {
    id: root
    modal: true
    standardButtons: Dialog.NoButton
    width: 420
    height: 244
    padding: 22

    property string actionLabel: ""

    background: Rectangle {
        color: Theme.cardGlassActive
        radius: Theme.radiusLg
        border.color: Theme.e5BorderPink
        border.width: 1
        antialiasing: true

        Rectangle {
            anchors.fill: parent
            anchors.margins: 1
            radius: parent.radius - 1
            color: Theme.glowPurple
            opacity: 0.18
        }

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 58
            radius: parent.radius
            color: "#26FFFFFF"
        }
    }

    contentItem: ColumnLayout {
        spacing: Theme.spaceMd

        Text {
            Layout.fillWidth: true
            text: "确认执行"
            color: Theme.textPrimary
            font.pixelSize: 20
            font.weight: Font.Bold
        }
        Text {
            Layout.fillWidth: true
            text: "即将执行：" + root.actionLabel + "\n\n请确认所有工作已保存。"
            color: Theme.textSecondary
            font.pixelSize: 14
            lineHeight: 1.16
            wrapMode: Text.WordWrap
        }
        Item { Layout.fillHeight: true }
    }

    footer: Item {
        implicitHeight: 64

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 22
            anchors.rightMargin: 22
            anchors.bottomMargin: 16
            spacing: Theme.spaceSm

            Item { Layout.fillWidth: true }

            NeonButton {
                compact: true
                text: "取消"
                onClicked: root.reject()
            }

            NeonButton {
                compact: true
                variant: "danger"
                text: "确认执行"
                onClicked: root.accept()
            }
        }
    }

    onAccepted: controller.executeNow()
}
