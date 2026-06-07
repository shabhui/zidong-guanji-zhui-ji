import QtQuick
import QtQuick.Layouts
import ".."

ColumnLayout {
    id: root
    spacing: 10

    property string powerActionStepSummaryText: ""
    signal executeNowRequested()

    Text { text: "任务中心"; color: Theme.textPrimary; font.pixelSize: 24; font.weight: Font.Bold }
    Text { Layout.fillWidth: true; text: "常用模板和临时动作放在左侧，队列和日志放在右侧。"; color: Theme.textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap }
    Text { text: "常用任务模板"; color: Theme.textPrimary; font.pixelSize: 16; font.weight: Font.Bold }

    GridLayout {
        Layout.fillWidth: true
        Layout.preferredHeight: 156
        columns: 2
        rowSpacing: 6
        columnSpacing: 8

        NeonButton { Layout.fillWidth: true; Layout.preferredHeight: 34; compact: true; variant: "primary"; text: "15 分钟后关机"; onClicked: controller.applyTaskTemplate("shutdown_15") }
        NeonButton { Layout.fillWidth: true; Layout.preferredHeight: 34; compact: true; variant: "primary"; text: "30 分钟后关机"; onClicked: controller.applyTaskTemplate("shutdown_30") }
        NeonButton { Layout.fillWidth: true; Layout.preferredHeight: 34; compact: true; variant: "secondary"; text: "1 小时后睡眠"; onClicked: controller.applyTaskTemplate("sleep_60") }
        NeonButton { Layout.fillWidth: true; Layout.preferredHeight: 34; compact: true; variant: "secondary"; text: "今晚 23:00 关机"; onClicked: controller.applyTaskTemplate("shutdown_2300") }
        NeonButton { Layout.fillWidth: true; Layout.preferredHeight: 34; compact: true; variant: "secondary"; text: "5 分钟后锁定"; onClicked: controller.applyTaskTemplate("lock_5") }
        NeonButton { Layout.fillWidth: true; Layout.preferredHeight: 34; compact: true; variant: "secondary"; text: "10 分钟后睡眠"; onClicked: controller.applyTaskTemplate("sleep_10") }
        NeonButton { Layout.fillWidth: true; Layout.preferredHeight: 34; compact: true; variant: "primary"; text: "明天 00:00 关机"; onClicked: controller.applyTaskTemplate("shutdown_midnight") }
    }

    Text { text: "临时动作选择"; color: Theme.textPrimary; font.pixelSize: 16; font.weight: Font.Bold }

    GridLayout {
        Layout.fillWidth: true
        Layout.preferredHeight: 116
        columns: 3
        rowSpacing: 6
        columnSpacing: 6

        ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 48; actionKey: "shutdown"; actionLabel: "关机"; actionSub: "SHUTDOWN" }
        ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 48; actionKey: "sleep"; actionLabel: "睡眠"; actionSub: "SLEEP" }
        ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 48; actionKey: "hibernate"; actionLabel: "休眠"; actionSub: "HIBERNATE" }
        ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 48; actionKey: "restart"; actionLabel: "重启"; actionSub: "RESTART" }
        ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 48; actionKey: "logoff"; actionLabel: "注销"; actionSub: "LOG OUT" }
        ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 48; actionKey: "lock"; actionLabel: "锁定"; actionSub: "LOCK" }
    }

    Flow {
        id: taskPrimaryActions
        Layout.fillWidth: true
        Layout.preferredHeight: 82
        spacing: 8

        NeonButton { width: 188; height: 38; compact: true; variant: "danger"; text: "立即执行当前动作"; enabled: !controller.powerActionInProgress; onClicked: root.executeNowRequested() }
        NeonButton { width: 94; height: 38; compact: true; variant: "secondary"; text: "取消任务"; enabled: controller.status === "running"; onClicked: controller.cancel() }
        NeonButton { width: 104; height: 34; compact: true; variant: "secondary"; text: "跳过等待"; visible: controller.canSkipCloseAppsWait; onClicked: controller.skipCloseAppsWait() }
    }

    Text {
        Layout.fillWidth: true
        visible: controller.powerActionInProgress
        text: controller.powerActionProgressText
        color: Theme.warning
        font.pixelSize: 12
        wrapMode: Text.WordWrap
    }

    Text { Layout.fillWidth: true; text: root.powerActionStepSummaryText; color: Theme.textSecondary; font.pixelSize: 11; wrapMode: Text.WordWrap }

    Text {
        Layout.fillWidth: true
        visible: !controller.dryRun
        text: "真实执行模式：请确认未保存工作，当前动作可能立即影响系统电源状态。"
        color: Theme.danger
        font.pixelSize: 12
        wrapMode: Text.WordWrap
    }
}
