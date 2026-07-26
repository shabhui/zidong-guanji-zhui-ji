import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

NeonCard {
    id: root
    height: showQuickLadder ? (showPresets ? 274 : (showSeconds ? 244 : 204)) : (showPresets ? 210 : (showSeconds ? 180 : 150))
    cardColor: Theme.blogGlassPanel
    cardBorderColor: Theme.blogCardBorder
    hoverable: false
    liquid: true

    property alias hours: hoursInput.text
    property alias minutes: minutesInput.text
    property alias seconds: secondsInput.text
    property bool showSeconds: true
    property bool showPresets: true
    property int maxHours: 23
    property bool showQuickLadder: true
    readonly property int totalMinutes: root.clampInt(hoursInput.text, 0, maxHours) * 60 + root.clampInt(minutesInput.text, 0, 59)

    function formatDuration() {
        var hoursValue = root.clampInt(hoursInput.text, 0, maxHours)
        var minutesValue = root.clampInt(minutesInput.text, 0, 59)
        var secondsValue = root.clampInt(secondsInput.text, 0, 59)
        if (hoursValue > 0 && minutesValue > 0) return String(hoursValue) + " \u5C0F\u65F6 " + String(minutesValue) + " \u5206\u949F"
        if (hoursValue > 0) return String(hoursValue) + " \u5C0F\u65F6"
        if (minutesValue > 0) return String(minutesValue) + " \u5206\u949F"
        if (showSeconds && secondsValue > 0) return String(secondsValue) + " \u79D2"
        return "0 \u5206\u949F"
    }

    function setTotalMinutes(value) {
        var total = root.clampInt(value, 0, maxHours * 60 + 59)
        setHours(Math.floor(total / 60))
        setMinutes(total % 60)
        if (showSeconds) setSeconds(0)
    }

    function clampInt(value, minValue, maxValue) {
        var n = parseInt(value)
        if (isNaN(n)) n = minValue
        return Math.max(minValue, Math.min(maxValue, n))
    }

    function setHours(value) {
        hoursInput.text = String(clampInt(value, 0, maxHours))
    }

    function setMinutes(value) {
        minutesInput.text = String(clampInt(value, 0, 59))
    }

    function setSeconds(value) {
        secondsInput.text = String(clampInt(value, 0, 59))
    }

    function nudgeHours(delta) { setHours(clampInt(hoursInput.text, 0, maxHours) + delta) }
    function nudgeMinutes(delta) { setMinutes(clampInt(minutesInput.text, 0, 59) + delta) }
    function nudgeSeconds(delta) { setSeconds(clampInt(secondsInput.text, 0, 59) + delta) }

    function applyPreset(h, m, s) {
        setHours(h)
        setMinutes(m)
        setSeconds(s)
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 10

        RowLayout {
            id: durationReadout
            visible: root.showQuickLadder
            Layout.fillWidth: true
            Layout.preferredHeight: 24
            Text { text: "\u5DF2\u9009\u65F6\u957F"; color: Theme.textSecondary; font.pixelSize: 12; font.weight: Font.DemiBold }
            Item { Layout.fillWidth: true }
            Text { text: root.formatDuration(); color: Theme.launchMint; font.pixelSize: 15; font.weight: Font.Bold }
        }

        Flow {
            id: durationQuickLadder
            visible: root.showQuickLadder
            Layout.fillWidth: true
            spacing: 6
            Repeater {
                model: [10, 30, 60, 90, 120]
                NeonButton {
                    required property int modelData
                    compact: true
                    variant: root.totalMinutes === modelData ? "launch" : "secondary"
                    text: modelData === 60 ? "1 \u5C0F\u65F6" : (modelData === 90 ? "1.5 \u5C0F\u65F6" : (modelData === 120 ? "2 \u5C0F\u65F6" : String(modelData) + " \u5206\u949F"))
                    onClicked: root.setTotalMinutes(modelData)
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            // Hours unit
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                Text { text: "时"; color: Theme.textSecondary; font.pixelSize: 12; Layout.alignment: Qt.AlignHCenter }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    NeonButton {
                        Layout.preferredWidth: 34
                        Layout.preferredHeight: 34
                        compact: true
                        text: "-"
                        onClicked: root.nudgeHours(-1)
                    }
                    TextField {
                        id: hoursInput
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        text: "0"
                        horizontalAlignment: Text.AlignHCenter
                        color: Theme.textPrimary
                        font.pixelSize: 22
                        font.weight: Font.Bold
                        background: Rectangle {
                            color: Theme.inputGlass
                            radius: Theme.radiusMd
                            border.color: Theme.borderSoft
                            border.width: 1
                        }
                        validator: RegularExpressionValidator { regularExpression: /[0-9]*/ }
                        maximumLength: 2
                        onEditingFinished: root.setHours(text)
                    }
                    NeonButton {
                        Layout.preferredWidth: 34
                        Layout.preferredHeight: 34
                        compact: true
                        text: "+"
                        onClicked: root.nudgeHours(1)
                    }
                }
                Slider {
                    id: hoursSlider
                    Layout.fillWidth: true
                    from: 0
                    to: root.maxHours
                    stepSize: 1
                    value: root.clampInt(hoursInput.text, 0, root.maxHours)
                    onMoved: root.setHours(Math.round(value))
                    background: Rectangle {
                        x: hoursSlider.leftPadding
                        y: hoursSlider.topPadding + hoursSlider.availableHeight / 2 - height / 2
                        implicitWidth: 120
                        implicitHeight: 6
                        width: hoursSlider.availableWidth
                        height: 6
                        radius: 3
                        color: "#28FFFFFF"
                        Rectangle {
                            width: hoursSlider.visualPosition * parent.width
                            height: parent.height
                            radius: 3
                            color: Theme.animeCyanGlow
                        }
                    }
                    handle: Rectangle {
                        x: hoursSlider.leftPadding + hoursSlider.visualPosition * (hoursSlider.availableWidth - width)
                        y: hoursSlider.topPadding + hoursSlider.availableHeight / 2 - height / 2
                        width: 16
                        height: 16
                        radius: 8
                        color: Theme.textPrimary
                        border.color: Theme.animeCyanGlow
                        border.width: 2
                    }
                }
            }

            Text { text: ":"; color: Theme.primary; font.pixelSize: 28; font.weight: Font.Bold; Layout.alignment: Qt.AlignVCenter }

            // Minutes unit
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                Text { text: "分"; color: Theme.textSecondary; font.pixelSize: 12; Layout.alignment: Qt.AlignHCenter }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    NeonButton {
                        Layout.preferredWidth: 34
                        Layout.preferredHeight: 34
                        compact: true
                        text: "-"
                        onClicked: root.nudgeMinutes(-1)
                    }
                    TextField {
                        id: minutesInput
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        text: "30"
                        horizontalAlignment: Text.AlignHCenter
                        color: Theme.textPrimary
                        font.pixelSize: 22
                        font.weight: Font.Bold
                        background: Rectangle {
                            color: Theme.inputGlass
                            radius: Theme.radiusMd
                            border.color: Theme.borderSoft
                            border.width: 1
                        }
                        validator: RegularExpressionValidator { regularExpression: /[0-9]*/ }
                        maximumLength: 2
                        onEditingFinished: root.setMinutes(text)
                    }
                    NeonButton {
                        Layout.preferredWidth: 34
                        Layout.preferredHeight: 34
                        compact: true
                        text: "+"
                        onClicked: root.nudgeMinutes(1)
                    }
                }
                Slider {
                    id: minutesSlider
                    Layout.fillWidth: true
                    from: 0
                    to: 59
                    stepSize: 1
                    value: root.clampInt(minutesInput.text, 0, 59)
                    onMoved: root.setMinutes(Math.round(value))
                    background: Rectangle {
                        x: minutesSlider.leftPadding
                        y: minutesSlider.topPadding + minutesSlider.availableHeight / 2 - height / 2
                        implicitWidth: 120
                        implicitHeight: 6
                        width: minutesSlider.availableWidth
                        height: 6
                        radius: 3
                        color: "#28FFFFFF"
                        Rectangle {
                            width: minutesSlider.visualPosition * parent.width
                            height: parent.height
                            radius: 3
                            color: Theme.animeSakura
                        }
                    }
                    handle: Rectangle {
                        x: minutesSlider.leftPadding + minutesSlider.visualPosition * (minutesSlider.availableWidth - width)
                        y: minutesSlider.topPadding + minutesSlider.availableHeight / 2 - height / 2
                        width: 16
                        height: 16
                        radius: 8
                        color: Theme.textPrimary
                        border.color: Theme.animeSakura
                        border.width: 2
                    }
                }
            }

            Text {
                visible: root.showSeconds
                text: ":"
                color: Theme.primary
                font.pixelSize: 28
                font.weight: Font.Bold
                Layout.alignment: Qt.AlignVCenter
            }

            // Seconds unit
            ColumnLayout {
                visible: root.showSeconds
                Layout.fillWidth: true
                spacing: 4
                Text { text: "秒"; color: Theme.textSecondary; font.pixelSize: 12; Layout.alignment: Qt.AlignHCenter }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    NeonButton {
                        Layout.preferredWidth: 34
                        Layout.preferredHeight: 34
                        compact: true
                        text: "-"
                        onClicked: root.nudgeSeconds(-1)
                    }
                    TextField {
                        id: secondsInput
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        text: "0"
                        horizontalAlignment: Text.AlignHCenter
                        color: Theme.textPrimary
                        font.pixelSize: 22
                        font.weight: Font.Bold
                        background: Rectangle {
                            color: Theme.inputGlass
                            radius: Theme.radiusMd
                            border.color: Theme.borderSoft
                            border.width: 1
                        }
                        validator: RegularExpressionValidator { regularExpression: /[0-9]*/ }
                        maximumLength: 2
                        onEditingFinished: root.setSeconds(text)
                    }
                    NeonButton {
                        Layout.preferredWidth: 34
                        Layout.preferredHeight: 34
                        compact: true
                        text: "+"
                        onClicked: root.nudgeSeconds(1)
                    }
                }
                Slider {
                    id: secondsSlider
                    Layout.fillWidth: true
                    from: 0
                    to: 59
                    stepSize: 1
                    value: root.clampInt(secondsInput.text, 0, 59)
                    onMoved: root.setSeconds(Math.round(value))
                    background: Rectangle {
                        x: secondsSlider.leftPadding
                        y: secondsSlider.topPadding + secondsSlider.availableHeight / 2 - height / 2
                        implicitWidth: 120
                        implicitHeight: 6
                        width: secondsSlider.availableWidth
                        height: 6
                        radius: 3
                        color: "#28FFFFFF"
                        Rectangle {
                            width: secondsSlider.visualPosition * parent.width
                            height: parent.height
                            radius: 3
                            color: Theme.animeVioletGlow
                        }
                    }
                    handle: Rectangle {
                        x: secondsSlider.leftPadding + secondsSlider.visualPosition * (secondsSlider.availableWidth - width)
                        y: secondsSlider.topPadding + secondsSlider.availableHeight / 2 - height / 2
                        width: 16
                        height: 16
                        radius: 8
                        color: Theme.textPrimary
                        border.color: Theme.animeVioletGlow
                        border.width: 2
                    }
                }
            }
        }

        Flow {
            id: timePresetChipRow
            visible: root.showPresets
            Layout.fillWidth: true
            spacing: 6
            Repeater {
                model: [
                    { label: "5分钟", h: 0, m: 5, s: 0 },
                    { label: "10分钟", h: 0, m: 10, s: 0 },
                    { label: "15分钟", h: 0, m: 15, s: 0 },
                    { label: "30分钟", h: 0, m: 30, s: 0 },
                    { label: "45分钟", h: 0, m: 45, s: 0 },
                    { label: "1小时", h: 1, m: 0, s: 0 },
                    { label: "2小时", h: 2, m: 0, s: 0 },
                    { label: "3小时", h: 3, m: 0, s: 0 }
                ]
                NeonButton {
                    required property var modelData
                    compact: true
                    text: modelData.label
                    onClicked: root.applyPreset(modelData.h, modelData.m, modelData.s)
                }
            }
        }
    }
}
