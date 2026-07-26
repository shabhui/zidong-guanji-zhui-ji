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
        eyebrow: "SMART TRIGGERS"; title: "智能触发"
        subtitle: "每种触发器独立配置、独立启动"
        statusText: controller.triggerHealthSummaryText; statusColor: Theme.workspaceSuccess
    }

    RowLayout {
        anchors.fill: parent; anchors.topMargin: 78; spacing: 12
        V5Section {
            Layout.fillWidth: true; Layout.fillHeight: true
            title: "进程退出"; subtitle: controller.processTriggerStatus; accentColor: Theme.animeAtmosphereSakura
            V5TextField { Layout.fillWidth: true; placeholderText: "进程名，例如 game.exe"; text: controller.processName; onEditingFinished: controller.processName = text }
            V5TextField { Layout.fillWidth: true; placeholderText: "检查间隔（秒）"; text: String(controller.processPollSeconds); onEditingFinished: controller.processPollSeconds = parseInt(text) || 5 }
            Text { Layout.fillWidth: true; text: "目标进程退出后，将创建当前电源动作。"; color: Theme.workspaceMuted; font.pixelSize: 11; wrapMode: Text.WordWrap }
            Item { Layout.fillHeight: true }
            NeonButton {
                Layout.fillWidth: true; variant: controller.processTriggerActive ? "quietDanger" : "primary"
                text: controller.processTriggerActive ? "停止进程监控" : "启动进程监控"
                onClicked: controller.processTriggerActive ? controller.stopProcessTrigger() : controller.startProcessTrigger()
            }
        }

        V5Section {
            Layout.fillWidth: true; Layout.fillHeight: true
            title: "网络空闲"; subtitle: controller.networkTriggerStatus + " · " + controller.networkSpeedText; accentColor: Theme.animeAtmosphereCyan
            V5TextField { Layout.fillWidth: true; placeholderText: "下载阈值 KB/s"; text: String(controller.networkDownloadThresholdKbps); onEditingFinished: controller.networkDownloadThresholdKbps = parseFloat(text) || 0 }
            V5TextField { Layout.fillWidth: true; placeholderText: "上传阈值 KB/s"; text: String(controller.networkUploadThresholdKbps); onEditingFinished: controller.networkUploadThresholdKbps = parseFloat(text) || 0 }
            V5TextField { Layout.fillWidth: true; placeholderText: "持续空闲秒数"; text: String(controller.networkIdleSeconds); onEditingFinished: controller.networkIdleSeconds = parseInt(text) || 60 }
            V5TextField { Layout.fillWidth: true; placeholderText: "检查间隔（秒）"; text: String(controller.networkPollSeconds); onEditingFinished: controller.networkPollSeconds = parseInt(text) || 3 }
            Item { Layout.fillHeight: true }
            NeonButton {
                Layout.fillWidth: true; variant: controller.networkTriggerActive ? "quietDanger" : "primary"
                text: controller.networkTriggerActive ? "停止网络监控" : "启动网络监控"
                onClicked: controller.networkTriggerActive ? controller.stopNetworkTrigger() : controller.startNetworkTrigger()
            }
        }

        V5Section {
            Layout.fillWidth: true; Layout.fillHeight: true
            title: "系统空闲"; subtitle: controller.idleTriggerStatus
            V5TextField { Layout.fillWidth: true; placeholderText: "空闲分钟"; text: String(controller.idleMinutes); onEditingFinished: controller.idleMinutes = parseInt(text) || 10 }
            V5TextField { Layout.fillWidth: true; placeholderText: "检查间隔（秒）"; text: String(controller.idlePollSeconds); onEditingFinished: controller.idlePollSeconds = parseInt(text) || 5 }
            GridLayout {
                Layout.fillWidth: true; columns: 3; columnSpacing: 5; rowSpacing: 5
                Repeater {
                    model: [
                        { key: "shutdown", label: "关机" }, { key: "sleep", label: "睡眠" },
                        { key: "hibernate", label: "休眠" }, { key: "restart", label: "重启" },
                        { key: "logoff", label: "注销" }, { key: "lock", label: "锁定" }
                    ]
                    NeonButton {
                        required property var modelData
                        Layout.fillWidth: true; compact: true
                        variant: controller.idleAction === modelData.key ? "primary" : "secondary"
                        text: modelData.label
                        onClicked: controller.idleAction = modelData.key
                    }
                }
            }
            Item { Layout.fillHeight: true }
            NeonButton {
                Layout.fillWidth: true; variant: controller.idleTriggerActive ? "quietDanger" : "primary"
                text: controller.idleTriggerActive ? "停止空闲监控" : "启动空闲监控"
                onClicked: controller.idleTriggerActive ? controller.stopIdleTrigger() : controller.startIdleTrigger()
            }
        }
    }
}
