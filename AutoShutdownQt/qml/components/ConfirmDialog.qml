import QtQuick
import QtQuick.Controls
import ".."

Dialog {
    id: root
    modal: true
    standardButtons: Dialog.Ok | Dialog.Cancel
    width: 400
    height: 220

    property string actionLabel: ""

    background: Rectangle {
        color: Theme.bgPanel
        radius: Theme.radiusLg
        border.color: Theme.borderStrong
        border.width: 1
    }

    Column {
        spacing: Theme.spaceMd
        Text {
            text: "确认执行"
            color: Theme.textPrimary
            font.pixelSize: 18
            font.weight: Font.Bold
        }
        Text {
            text: "即将执行：" + root.actionLabel + "\n\n请确认所有工作已保存。"
            color: Theme.textSecondary
            font.pixelSize: 14
            wrapMode: Text.WordWrap
            width: 340
        }
    }

    onAccepted: controller.executeNow()
}
