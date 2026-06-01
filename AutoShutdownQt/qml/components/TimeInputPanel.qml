import QtQuick
import QtQuick.Controls
import ".."

NeonCard {
    id: root
    height: 110

    property alias hours: hoursInput.text
    property alias minutes: minutesInput.text
    property alias seconds: secondsInput.text
    property bool showSeconds: true

    Row {
        spacing: Theme.spaceSm
        anchors.centerIn: parent

        Column {
            spacing: Theme.spaceXs
            Text { text: "时"; color: Theme.textSecondary; font.pixelSize: 12; anchors.horizontalCenter: parent.horizontalCenter }
            TextField {
                id: hoursInput
                width: 72; height: 44
                text: "0"
                horizontalAlignment: Text.AlignHCenter
                color: Theme.textPrimary
                font.pixelSize: 22
                font.weight: Font.Bold
                background: Rectangle { color: Theme.surfaceGlass; radius: Theme.radiusSm; border.color: Theme.borderSoft; border.width: 1 }
                validator: RegularExpressionValidator { regularExpression: /[0-9]*/ }
                maximumLength: 2
            }
        }

        Text { text: ":"; color: Theme.primary; font.pixelSize: 28; font.weight: Font.Bold; anchors.verticalCenter: parent.verticalCenter }

        Column {
            spacing: Theme.spaceXs
            Text { text: "分"; color: Theme.textSecondary; font.pixelSize: 12; anchors.horizontalCenter: parent.horizontalCenter }
            TextField {
                id: minutesInput
                width: 72; height: 44
                text: "30"
                horizontalAlignment: Text.AlignHCenter
                color: Theme.textPrimary
                font.pixelSize: 22
                font.weight: Font.Bold
                background: Rectangle { color: Theme.surfaceGlass; radius: Theme.radiusSm; border.color: Theme.borderSoft; border.width: 1 }
                validator: RegularExpressionValidator { regularExpression: /[0-9]*/ }
                maximumLength: 2
            }
        }

        Text {
            visible: root.showSeconds
            text: ":"; color: Theme.primary; font.pixelSize: 28; font.weight: Font.Bold; anchors.verticalCenter: parent.verticalCenter
        }

        Column {
            visible: root.showSeconds
            spacing: Theme.spaceXs
            Text { text: "秒"; color: Theme.textSecondary; font.pixelSize: 12; anchors.horizontalCenter: parent.horizontalCenter }
            TextField {
                id: secondsInput
                width: 72; height: 44
                text: "0"
                horizontalAlignment: Text.AlignHCenter
                color: Theme.textPrimary
                font.pixelSize: 22
                font.weight: Font.Bold
                background: Rectangle { color: Theme.surfaceGlass; radius: Theme.radiusSm; border.color: Theme.borderSoft; border.width: 1 }
                validator: RegularExpressionValidator { regularExpression: /[0-9]*/ }
                maximumLength: 2
            }
        }
    }
}
