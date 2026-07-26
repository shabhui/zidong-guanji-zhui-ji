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
        eyebrow: "AUTOMATION"; title: "脚本与诊断"
        subtitle: "执行前脚本、健康检查和日志集中管理"
        statusText: controller.scriptEnabled ? "脚本已启用" : "脚本未启用"
        statusColor: controller.scriptEnabled ? Theme.workspaceSuccess : Theme.workspaceMuted
    }

    RowLayout {
        anchors.fill: parent; anchors.topMargin: 78; spacing: 12
        ColumnLayout {
            Layout.preferredWidth: 350; Layout.fillHeight: true; spacing: 12
            V5Section {
                Layout.fillWidth: true; Layout.preferredHeight: 230
                title: "执行前脚本"; subtitle: "真实执行前运行；安全验证模式只记录流程"; accentColor: Theme.animeAtmosphereSakura
                RowLayout {
                    Layout.fillWidth: true
                    Text { Layout.fillWidth: true; text: "启用脚本"; color: Theme.workspaceInk; font.pixelSize: 13; font.weight: Font.Medium }
                    FluentSwitch { checked: controller.scriptEnabled; onCheckedChanged: if (checked !== controller.scriptEnabled) controller.scriptEnabled = checked }
                }
                V5TextField { Layout.fillWidth: true; placeholderText: "脚本路径"; text: controller.scriptPath; onEditingFinished: controller.scriptPath = text }
                V5TextField { Layout.fillWidth: true; placeholderText: "超时秒数"; text: String(controller.scriptTimeoutSeconds); onEditingFinished: controller.scriptTimeoutSeconds = parseInt(text) || 30 }
                RowLayout {
                    Layout.fillWidth: true
                    NeonButton { Layout.fillWidth: true; compact: true; variant: "primary"; text: "测试脚本"; onClicked: controller.testScript() }
                    NeonButton { Layout.fillWidth: true; compact: true; text: "验证路径"; onClicked: controller.validateScriptPath() }
                    NeonButton { Layout.fillWidth: true; compact: true; text: "打开目录"; onClicked: controller.openScriptFolder() }
                }
            }

            V5Section {
                Layout.fillWidth: true; Layout.fillHeight: true
                title: "健康检查"; subtitle: controller.healthCheckText; accentColor: Theme.animeAtmosphereCyan
                Text { Layout.fillWidth: true; Layout.fillHeight: true; text: controller.diagnosticText; color: Theme.workspaceMuted; font.pixelSize: 10; wrapMode: Text.WrapAnywhere; elide: Text.ElideRight; maximumLineCount: 12 }
                RowLayout {
                    Layout.fillWidth: true
                    NeonButton { Layout.fillWidth: true; compact: true; text: "运行检查"; onClicked: controller.runHealthCheck() }
                    NeonButton { Layout.fillWidth: true; compact: true; text: "复制诊断"; onClicked: controller.copyDiagnostics() }
                    NeonButton { Layout.fillWidth: true; compact: true; text: "导出"; onClicked: controller.exportDiagnostics() }
                }
            }
        }

        V5Section {
            Layout.fillWidth: true; Layout.fillHeight: true
            title: "运行日志"; subtitle: controller.logSummaryText
            RowLayout {
                Layout.fillWidth: true
                NeonButton { compact: true; variant: controller.logFilter === "all" ? "primary" : "secondary"; text: "全部"; onClicked: controller.setLogFilter("all") }
                NeonButton { compact: true; variant: controller.logFilter === "warning" ? "primary" : "secondary"; text: "警告"; onClicked: controller.setLogFilter("warning") }
                NeonButton { compact: true; variant: controller.logFilter === "error" ? "primary" : "secondary"; text: "错误"; onClicked: controller.setLogFilter("error") }
                Item { Layout.fillWidth: true }
                NeonButton { compact: true; text: "导出日志"; onClicked: controller.exportLogs() }
                NeonButton { compact: true; variant: "quietDanger"; text: "清空"; onClicked: controller.clearLogs() }
            }
            Text { Layout.fillWidth: true; text: controller.logCategorySummaryText; color: Theme.workspaceMuted; font.pixelSize: 10; elide: Text.ElideRight }
            Text { visible: controller.copyStatusText !== ""; Layout.fillWidth: true; text: controller.copyStatusText; color: Theme.workspaceSuccess; font.pixelSize: 10; elide: Text.ElideRight }
            TextArea {
                Layout.fillWidth: true; Layout.fillHeight: true
                readOnly: true; text: controller.filteredLogText; color: Theme.workspaceInk
                font.pixelSize: 11; font.family: "Consolas"; wrapMode: TextArea.Wrap
                background: Rectangle { radius: Theme.controlRadius; color: Theme.workspaceSurfaceRaised; border.color: Theme.controlBorder; border.width: 1 }
            }
        }
    }
}
