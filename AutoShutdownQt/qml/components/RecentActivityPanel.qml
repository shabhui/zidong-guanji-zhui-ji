import QtQuick
import QtQuick.Layouts
import ".."

NeonCard {
    id: root
    Layout.fillWidth: true
    Layout.fillHeight: true
    cardColor: Theme.dialogPanelRaised
    cardBorderColor: Theme.e5BorderSoft

    property string categorySummaryText: ""

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 6

        Text {
            property string regressionAnchor: "Recent activity · 最近日志"
            text: "最近日志"
            color: Theme.textPrimary
            font.pixelSize: 15
            font.weight: Font.Bold
        }

        Text {
            Layout.fillWidth: true
            text: controller.logSummaryText
            color: Theme.textSecondary
            font.pixelSize: 12
            wrapMode: Text.WordWrap
        }

        Text {
            Layout.fillWidth: true
            property string diagnosticSource: controller.logCategorySummaryText
            text: root.categorySummaryText
            color: Theme.textSecondary
            font.pixelSize: 11
            wrapMode: Text.WordWrap
        }

        Text {
            Layout.fillWidth: true
            Layout.fillHeight: true
            text: controller.logText
            color: Theme.textSecondary
            font.pixelSize: 12
            wrapMode: Text.WordWrap
            elide: Text.ElideRight
        }
    }
}
