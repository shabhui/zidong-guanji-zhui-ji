import QtQuick
import QtQuick.Layouts
import ".."

ColumnLayout {
    id: root
    spacing: 10

    property var queueRows: []

    Text {
        property string regressionAnchor: "Task Queue Dashboard · 任务队列"
        text: "任务队列"
        color: Theme.textPrimary
        font.pixelSize: 18
        font.weight: Font.Bold
    }

    Text {
        Layout.fillWidth: true
        text: controller.queueSummaryText
        color: Theme.textSecondary
        font.pixelSize: 12
        wrapMode: Text.WordWrap
    }

    ListView {
        id: taskQueueDashboard
        Layout.fillWidth: true
        Layout.preferredHeight: 140
        clip: true
        model: root.queueRows

        Text {
            anchors.centerIn: parent
            visible: root.queueRows.length === 0
            text: "暂无排队任务"
            color: Theme.textSecondary
            font.pixelSize: 13
            font.weight: Font.Bold
        }

        delegate: Rectangle {
            width: ListView.view.width
            height: modelData.status === "failed" ? 118 : 90
            radius: Theme.radiusMd
            color: Theme.glassSoft
            border.color: Theme.e5BorderSoft
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 6

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 1

                        Text { text: modelData.name; color: Theme.textPrimary; font.pixelSize: 13; font.weight: Font.Bold; elide: Text.ElideRight; Layout.fillWidth: true; maximumLineCount: 1 }
                        Text { text: modelData.triggerSummary + " · " + modelData.repeatSummary; color: Theme.textSecondary; font.pixelSize: 11; elide: Text.ElideRight; Layout.fillWidth: true; maximumLineCount: 1 }
                        Text { text: modelData.status + " · " + modelData.nextRunText; color: modelData.enabled ? Theme.warning : Theme.textSecondary; font.pixelSize: 11; elide: Text.ElideRight; Layout.fillWidth: true; maximumLineCount: 1 }
                        Text { visible: modelData.status === "failed"; text: modelData.lastError; color: Theme.danger; font.pixelSize: 11; elide: Text.ElideRight; Layout.fillWidth: true; maximumLineCount: 1 }
                    }

                    FluentSwitch {
                        checked: modelData.enabled
                        onCheckedChanged: controller.setQueueTaskEnabled(modelData.id, checked)
                    }
                }

                Flow {
                    id: taskQueueActions
                    Layout.fillWidth: true
                    Layout.preferredHeight: modelData.status === "failed" ? 62 : 30
                    spacing: 6

                    NeonButton { width: 104; height: 30; compact: true; variant: "secondary"; text: "Dry-run 检查"; onClicked: controller.runQueueTaskDryRunCheck(modelData.id) }
                    NeonButton { width: 58; height: 30; compact: true; variant: "primary"; text: "重试"; visible: modelData.status === "failed"; onClicked: controller.retryQueueTask(modelData.id) }
                    NeonButton { width: 90; height: 30; compact: true; variant: "secondary"; text: "复制诊断"; visible: modelData.status === "failed"; onClicked: controller.copyQueueTaskDiagnostic(modelData.id) }
                    NeonButton { width: 58; height: 30; compact: true; variant: "danger"; text: "删除"; onClicked: controller.deleteQueueTask(modelData.id) }
                }
            }
        }
    }
}
