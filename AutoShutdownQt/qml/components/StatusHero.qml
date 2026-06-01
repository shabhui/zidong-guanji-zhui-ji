import QtQuick
import ".."

NeonCard {
    id: root
    height: 280
    cardColor: "#30FFFFFF"
    cardBorderColor: Theme.borderStrong

    Column {
        anchors.fill: parent
        anchors.margins: Theme.spaceLg
        spacing: Theme.spaceMd

        // Status pill
        Rectangle {
            radius: Theme.radiusMd
            color: Theme.surfaceStrong
            border.color: controller.statusColor
            border.width: 1
            width: statusLabel.width + 24
            height: 30
            Text {
                id: statusLabel
                anchors.centerIn: parent
                text: controller.status === "running" ? "RUNNING" : "READY"
                color: controller.statusColor
                font.pixelSize: 13
                font.weight: Font.Bold
            }
        }

        // Action label
        Text {
            text: controller.actionLabel
            color: Theme.textPrimary
            font.pixelSize: 26
            font.weight: Font.Bold
        }

        // Remaining time
        Text {
            text: controller.remainingText
            color: controller.status === "running" ? Theme.warning : Theme.textSecondary
            font.pixelSize: 64
            font.weight: Font.Bold
            font.family: "Consolas"
        }

        // Target / hint
        Text {
            text: controller.targetInfo ? "目标：" + controller.targetInfo : "选择动作和时间，启动倒计时或指定时间"
            color: Theme.textSecondary
            font.pixelSize: 14
            wrapMode: Text.WordWrap
            width: parent.width
        }
    }
}
