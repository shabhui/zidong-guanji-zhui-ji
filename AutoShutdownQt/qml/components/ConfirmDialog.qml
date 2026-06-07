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

    Overlay.modal: Rectangle {
        color: Theme.dialogScrim
    }

    background: Rectangle {
        color: Theme.dialogPanel
        radius: Theme.radiusLg
        border.color: Theme.e5BorderPink
        border.width: 1
        antialiasing: true

        Rectangle {
            anchors.fill: parent
            anchors.margins: 1
            radius: parent.radius - 1
            color: Theme.dialogPanelRaised
            opacity: 0.54
        }

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 58
            radius: parent.radius
            color: "#18FFFFFF"
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
            text: "即将执行：" + root.actionLabel + "\n\n" + (controller.dryRun
                ? "Dry-run 将只记录当前动作，不会真实执行系统电源操作。"
                : "LIVE MODE 会真实执行当前动作，可能导致关机、重启、睡眠、休眠、注销或锁定。请确认未保存工作。")
            color: controller.dryRun ? Theme.textSecondary : Theme.danger
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
