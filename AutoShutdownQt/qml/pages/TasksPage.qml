import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"

Item {
    id: root
    property var rootWindow

    V5PageTitle {
        anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
        eyebrow: "QUEUE"; title: "任务"
        subtitle: "队列、模板与执行记录放在同一页"
        statusText: "队列 " + String(rootWindow.queueRowModel.length); statusColor: Theme.animeAtmosphereCyan
    }

    ColumnLayout {
        anchors.fill: parent; anchors.topMargin: 78; spacing: 12

        V5Section {
            Layout.fillWidth: true; Layout.preferredHeight: 106
            title: "快速模板"; subtitle: "一键生成常见任务"; accentColor: Theme.animeAtmosphereSakura
            RowLayout {
                Layout.fillWidth: true; spacing: 8
                NeonButton { text: "5 分钟后锁定"; onClicked: controller.applyTaskTemplate("lock_5") }
                NeonButton { text: "10 分钟后睡眠"; onClicked: controller.applyTaskTemplate("sleep_10") }
                NeonButton { text: "明天 00:00 关机"; onClicked: controller.applyTaskTemplate("shutdown_midnight") }
                Item { Layout.fillWidth: true }
                NeonButton { compact: true; text: controller.schedulingPaused ? "恢复调度" : "暂停调度"; onClicked: controller.schedulingPaused ? controller.resumeScheduling() : controller.pauseScheduling() }
                NeonButton { compact: true; variant: "quietDanger"; text: "清空任务"; onClicked: controller.cancelAllTasks() }
            }
        }

        RowLayout {
            Layout.fillWidth: true; Layout.fillHeight: true; spacing: 12
            V5Section {
                Layout.fillWidth: true; Layout.fillHeight: true
                title: "任务队列"; subtitle: controller.queueSummaryText
                ListView {
                    Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 7
                    model: rootWindow.queueRowModel
                    delegate: Rectangle {
                        required property var modelData
                        width: ListView.view.width; height: 74
                        radius: Theme.controlRadius; color: Theme.controlSurface; border.color: Theme.controlBorder; border.width: 1
                        RowLayout {
                            anchors.fill: parent; anchors.margins: 10; spacing: 8
                            Rectangle { Layout.preferredWidth: 4; Layout.fillHeight: true; radius: 2; color: modelData.enabled ? Theme.workspaceAccent : Theme.workspaceMuted }
                            ColumnLayout {
                                Layout.fillWidth: true; spacing: 1
                                Text { Layout.fillWidth: true; text: modelData.name || "未命名任务"; color: Theme.workspaceInk; font.pixelSize: 13; font.weight: Font.DemiBold; elide: Text.ElideRight }
                                Text { Layout.fillWidth: true; text: (modelData.trigger || "") + " · " + (modelData.action || ""); color: Theme.workspaceMuted; font.pixelSize: 10; elide: Text.ElideRight }
                                Text { Layout.fillWidth: true; text: modelData.lastError || modelData.statusText || modelData.status || "等待"; color: modelData.status === "failed" ? Theme.workspaceDanger : Theme.workspaceMuted; font.pixelSize: 10; elide: Text.ElideRight }
                            }
                            NeonButton { compact: true; text: modelData.enabled ? "停用" : "启用"; onClicked: controller.setQueueTaskEnabled(String(modelData.id), !modelData.enabled) }
                            NeonButton { compact: true; text: "检查"; onClicked: controller.runQueueTaskDryRunCheck(String(modelData.id)) }
                            NeonButton { visible: modelData.status === "failed"; compact: true; variant: "primary"; text: "重试"; onClicked: controller.retryQueueTask(String(modelData.id)) }
                            NeonButton { visible: modelData.status === "failed"; compact: true; text: "复制诊断"; onClicked: controller.copyQueueTaskDiagnostic(String(modelData.id)) }
                            NeonButton { compact: true; variant: "quietDanger"; text: "删除"; onClicked: controller.deleteQueueTask(String(modelData.id)) }
                        }
                    }
                    Text { anchors.centerIn: parent; visible: rootWindow.queueRowModel.length === 0; text: "暂无任务，从上方模板或定时页开始"; color: Theme.workspaceMuted; font.pixelSize: 12 }
                }
            }

            V5Section {
                Layout.preferredWidth: 300; Layout.fillHeight: true
                title: "最近执行"; subtitle: "保留最近的结果，方便排查"; accentColor: Theme.animeAtmosphereCyan
                ListView {
                    Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 6
                    model: rootWindow.historyRowModel
                    delegate: Rectangle {
                        required property var modelData
                        width: ListView.view.width; height: 58; radius: Theme.controlRadius; color: Theme.workspaceSurfaceRaised
                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 9; spacing: 1
                            Text { Layout.fillWidth: true; text: modelData.message || modelData.event || "执行记录"; color: Theme.workspaceInk; font.pixelSize: 11; font.weight: Font.Medium; elide: Text.ElideRight }
                            Text { Layout.fillWidth: true; text: modelData.time || modelData.timestamp || ""; color: Theme.workspaceMuted; font.pixelSize: 9; elide: Text.ElideRight }
                        }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    NeonButton { Layout.fillWidth: true; compact: true; text: "导出历史"; onClicked: controller.exportHistory() }
                    NeonButton { Layout.fillWidth: true; compact: true; variant: "quietDanger"; text: "清空"; onClicked: controller.clearHistory() }
                }
            }
        }
    }
}
