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
        eyebrow: "PREFERENCES"; title: "设置"
        subtitle: "安全、关闭应用、提醒和启动行为"
        statusText: controller.dryRun ? "安全验证" : "真实执行"
        statusColor: controller.dryRun ? Theme.workspaceSuccess : Theme.workspaceDanger
    }

    ScrollView {
        anchors.fill: parent; anchors.topMargin: 78; clip: true
        ColumnLayout {
            width: parent.width; spacing: 12
            V5Section {
                Layout.fillWidth: true
                title: "安全执行"; subtitle: "建议日常保持安全验证开启"
                accentColor: controller.dryRun ? Theme.workspaceSuccess : Theme.workspaceDanger
                RowLayout {
                    Layout.fillWidth: true
                    ColumnLayout {
                        Layout.fillWidth: true
                        Text { Layout.fillWidth: true; text: "安全验证模式"; color: Theme.workspaceInk; font.pixelSize: 13; font.weight: Font.DemiBold }
                        Text { Layout.fillWidth: true; text: "开启时只验证流程，不执行真实电源动作。"; color: Theme.workspaceMuted; font.pixelSize: 10; wrapMode: Text.WordWrap }
                    }
                    FluentSwitch { id: v5DryRunSwitch; checked: controller.dryRun; onCheckedChanged: if (checked !== controller.dryRun) rootWindow.confirmLiveModeFromSwitch(checked) }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Text { Layout.fillWidth: true; text: "强制关闭应用"; color: Theme.workspaceInk; font.pixelSize: 13 }
                    FluentSwitch { checked: controller.forceClose; onCheckedChanged: if (checked !== controller.forceClose) controller.forceClose = checked }
                }
            }

            V5Section {
                Layout.fillWidth: true
                title: "关闭应用"; subtitle: "系统动作前先尝试优雅关闭打开的程序"; accentColor: Theme.animeAtmosphereSakura
                RowLayout {
                    Layout.fillWidth: true
                    Text { Layout.fillWidth: true; text: "执行前关闭应用"; color: Theme.workspaceInk; font.pixelSize: 13 }
                    FluentSwitch { checked: controller.closeAppsBeforeAction; onCheckedChanged: if (checked !== controller.closeAppsBeforeAction) controller.closeAppsBeforeAction = checked }
                }
                RowLayout {
                    Layout.fillWidth: true
                    V5TextField { Layout.fillWidth: true; placeholderText: "等待秒数"; text: String(controller.closeAppsTimeoutSeconds); onEditingFinished: controller.closeAppsTimeoutSeconds = parseInt(text) || 15 }
                    NeonButton { text: "预览可关闭应用"; onClicked: controller.previewCloseApps() }
                    NeonButton { visible: controller.canSkipCloseAppsWait; variant: "quietDanger"; text: "跳过等待"; onClicked: controller.skipCloseAppsWait() }
                }
                Text { Layout.fillWidth: true; text: controller.closeAppsPreviewText + " " + controller.closeAppsLastResultText; color: Theme.workspaceMuted; font.pixelSize: 10; wrapMode: Text.WordWrap }
            }

            V5Section {
                Layout.fillWidth: true
                title: "提醒与启动"; subtitle: "减少漏看任务和重复设置"; accentColor: Theme.animeAtmosphereCyan
                RowLayout {
                    Layout.fillWidth: true
                    V5TextField { Layout.fillWidth: true; placeholderText: "提醒提前量，例如 10,5,1"; text: controller.reminderMinutesCsv; onEditingFinished: controller.reminderMinutesCsv = text }
                    V5TextField { Layout.preferredWidth: 150; placeholderText: "默认延后分钟"; text: String(controller.snoozeMinutesValue); onEditingFinished: controller.snoozeMinutesValue = parseInt(text) || 15 }
                    V5TextField { Layout.preferredWidth: 150; placeholderText: "历史记录上限"; text: String(controller.taskHistoryLimit); onEditingFinished: controller.taskHistoryLimit = parseInt(text) || 500 }
                }
                GridLayout {
                    Layout.fillWidth: true; columns: 2; columnSpacing: 18; rowSpacing: 10
                    RowLayout {
                        Layout.fillWidth: true
                        Text { Layout.fillWidth: true; text: "任务提醒"; color: Theme.workspaceInk; font.pixelSize: 12 }
                        FluentSwitch { checked: controller.reminderEnabled; onCheckedChanged: if (checked !== controller.reminderEnabled) controller.reminderEnabled = checked }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Text { Layout.fillWidth: true; text: "Windows 通知"; color: Theme.workspaceInk; font.pixelSize: 12 }
                        FluentSwitch { checked: controller.windowsNotificationsEnabled; onCheckedChanged: if (checked !== controller.windowsNotificationsEnabled) controller.windowsNotificationsEnabled = checked }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Text { Layout.fillWidth: true; text: "开机自动启动"; color: Theme.workspaceInk; font.pixelSize: 12 }
                        FluentSwitch { checked: controller.startWithWindows; onCheckedChanged: if (checked !== controller.startWithWindows) controller.startWithWindows = checked }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Text { Layout.fillWidth: true; text: "启动后最小化到托盘"; color: Theme.workspaceInk; font.pixelSize: 12 }
                        FluentSwitch { checked: controller.startMinimizedToTray; onCheckedChanged: if (checked !== controller.startMinimizedToTray) controller.startMinimizedToTray = checked }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Text { Layout.fillWidth: true; text: "启动时自动播放音乐"; color: Theme.workspaceInk; font.pixelSize: 12 }
                        FluentSwitch { checked: controller.musicAutoplayEnabled; onCheckedChanged: if (checked !== controller.musicAutoplayEnabled) controller.musicAutoplayEnabled = checked }
                    }
                }
            }

            V5Section {
                Layout.fillWidth: true
                title: "维护"; subtitle: "检查配置并导出诊断"
                RowLayout {
                    Layout.fillWidth: true
                    NeonButton { text: "健康检查"; onClicked: controller.runHealthCheck() }
                    NeonButton { text: "导出诊断"; onClicked: controller.exportDiagnostics() }
                    NeonButton { text: "复制诊断"; onClicked: controller.copyDiagnostics() }
                    Item { Layout.fillWidth: true }
                    NeonButton { variant: "quietDanger"; text: "退出应用"; onClicked: controller.requestQuit() }
                }
            }
        }
    }

    function syncDryRunSwitchState() { v5DryRunSwitch.checked = controller.dryRun }
}
