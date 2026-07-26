import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"

Item {
    id: root
    property var rootWindow
    property string repeatRule: "once"
    property int fixedHourValue: 23
    property int fixedMinuteValue: 30

    function number(text, fallback) {
        var value = parseInt(text)
        return isNaN(value) ? fallback : value
    }

    function pad2(value) {
        return value < 10 ? "0" + value : String(value)
    }

    V5PageTitle {
        anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
        eyebrow: "SCHEDULE"; title: "定时"
        subtitle: "倒计时和指定时间分开设置，减少填错时间的机会"
        statusText: "动作 · " + controller.actionLabel; statusColor: Theme.workspaceAccent
    }

    RowLayout {
        anchors.fill: parent; anchors.topMargin: 78; spacing: 12

        V5Section {
            Layout.fillWidth: true; Layout.fillHeight: true
            title: "倒计时"; subtitle: "适合临时任务"; accentColor: Theme.animeAtmosphereSakura
            RowLayout {
                Layout.fillWidth: true; spacing: 8
                V5TextField { id: countdownHours; Layout.fillWidth: true; placeholderText: "小时"; text: "0" }
                V5TextField { id: countdownMinutes; Layout.fillWidth: true; placeholderText: "分钟"; text: "30" }
                V5TextField { id: countdownSeconds; Layout.fillWidth: true; placeholderText: "秒"; text: "0" }
            }
            RowLayout {
                Layout.fillWidth: true
                Repeater {
                    model: [15, 30, 60, 120]
                    NeonButton {
                        required property int modelData
                        compact: true
                        text: modelData < 60 ? modelData + " 分钟" : modelData / 60 + " 小时"
                        onClicked: { countdownHours.text = String(Math.floor(modelData / 60)); countdownMinutes.text = String(modelData % 60); countdownSeconds.text = "0" }
                    }
                }
                Item { Layout.fillWidth: true }
            }
            Item { Layout.fillHeight: true }
            NeonButton {
                Layout.fillWidth: true; variant: "primary"; leadingIcon: "▶"; text: "启动倒计时"
                onClicked: controller.startCountdown(root.number(countdownHours.text, 0), root.number(countdownMinutes.text, 0), root.number(countdownSeconds.text, 0))
            }
        }

        V5Section {
            Layout.fillWidth: true; Layout.fillHeight: true
            title: "指定时间"; subtitle: "到达时间后执行当前动作"; accentColor: Theme.animeAtmosphereCyan
            RowLayout {
                Layout.fillWidth: true
                spacing: 18

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    RowLayout {
                        Layout.fillWidth: true

                        Text {
                            text: root.pad2(root.fixedHourValue)
                            color: Theme.workspaceInk
                            font.pixelSize: 30
                            font.family: "Consolas"
                            font.weight: Font.Bold
                        }

                        Item { Layout.fillWidth: true }

                        Text { text: "小时"; color: Theme.workspaceMuted; font.pixelSize: 10 }
                    }

                    V5TimeSlider {
                        id: fixedHourSlider
                        Layout.fillWidth: true
                        from: 0
                        to: 23
                        stepSize: 1
                        value: root.fixedHourValue
                        accentColor: Theme.workspaceCyan
                        onMoved: root.fixedHourValue = Math.round(value)
                    }
                }

                Text {
                    text: ":"
                    color: Theme.workspaceMuted
                    font.pixelSize: 28
                    Layout.alignment: Qt.AlignVCenter
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    RowLayout {
                        Layout.fillWidth: true

                        Text {
                            text: root.pad2(root.fixedMinuteValue)
                            color: Theme.workspaceInk
                            font.pixelSize: 30
                            font.family: "Consolas"
                            font.weight: Font.Bold
                        }

                        Item { Layout.fillWidth: true }

                        Text { text: "分钟"; color: Theme.workspaceMuted; font.pixelSize: 10 }
                    }

                    V5TimeSlider {
                        id: fixedMinuteSlider
                        Layout.fillWidth: true
                        from: 0
                        to: 59
                        stepSize: 1
                        value: root.fixedMinuteValue
                        accentColor: Theme.workspaceAccent
                        onMoved: root.fixedMinuteValue = Math.round(value)
                    }
                }
            }
            Text { Layout.fillWidth: true; text: "拖动滑块选择时间；若时间已过，将自动安排到下一天。"; color: Theme.workspaceMuted; font.pixelSize: 11; wrapMode: Text.WordWrap }
            RowLayout {
                Layout.fillWidth: true
                Repeater {
                    model: [
                        { key: "once", label: "仅一次" }, { key: "daily", label: "每天" },
                        { key: "weekdays", label: "工作日" }, { key: "weekends", label: "周末" }
                    ]
                    NeonButton {
                        required property var modelData
                        compact: true
                        variant: root.repeatRule === modelData.key ? "primary" : "secondary"
                        text: modelData.label
                        onClicked: root.repeatRule = modelData.key
                    }
                }
                Item { Layout.fillWidth: true }
            }
            Item { Layout.fillHeight: true }
            NeonButton {
                Layout.fillWidth: true; variant: "primary"; leadingIcon: "+"; text: "添加指定时间任务"
                onClicked: {
                    var hour = root.fixedHourValue
                    var minute = root.fixedMinuteValue
                    if (root.repeatRule === "once") controller.startFixedTime(hour, minute)
                    else controller.addFixedTimeTask("固定时间 " + root.pad2(hour) + ":" + root.pad2(minute), hour, minute, root.repeatRule)
                }
            }
        }

        V5Section {
            Layout.preferredWidth: 250; Layout.fillHeight: true
            title: "当前动作"; subtitle: "定时任务会使用此动作"
            ColumnLayout {
                Layout.fillWidth: true
                Repeater {
                    model: [
                        { key: "shutdown", label: "关机" }, { key: "sleep", label: "睡眠" },
                        { key: "hibernate", label: "休眠" }, { key: "restart", label: "重启" },
                        { key: "logoff", label: "注销" }, { key: "lock", label: "锁定" }
                    ]
                    NeonButton {
                        required property var modelData
                        Layout.fillWidth: true; compact: true
                        variant: controller.selectedAction === modelData.key ? "primary" : "secondary"
                        text: modelData.label
                        onClicked: controller.selectedAction = modelData.key
                    }
                }
            }
        }
    }
}
