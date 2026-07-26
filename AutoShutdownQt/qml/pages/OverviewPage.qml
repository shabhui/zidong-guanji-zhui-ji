import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"

Item {
    id: root
    property var rootWindow
    property int quickMinutes: 30
    readonly property string displayedCountdown: controller.status === "running"
                                                  ? controller.remainingText
                                                  : root.formatDuration(root.quickMinutes)

    function pad2(value) {
        return value < 10 ? "0" + value : String(value)
    }

    function formatDuration(minutes) {
        var hours = Math.floor(minutes / 60)
        var remainingMinutes = minutes % 60
        return pad2(hours) + ":" + pad2(remainingMinutes) + ":00"
    }

    Rectangle {
        anchors.fill: parent
        color: Theme.workspaceBackground
    }

    Image {
        anchors.fill: parent
        source: "../assets/wuthering-waves-official.webp"
        fillMode: Image.PreserveAspectCrop
        horizontalAlignment: Image.AlignRight
        verticalAlignment: Image.AlignVCenter
        opacity: 0.68
        smooth: true
        mipmap: true
    }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#F8050B16" }
            GradientStop { position: 0.42; color: "#D90A1726" }
            GradientStop { position: 0.72; color: "#74101929" }
            GradientStop { position: 1.0; color: "#D4070C17" }
        }
    }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#18000000" }
            GradientStop { position: 0.66; color: "#22050B16" }
            GradientStop { position: 1.0; color: "#F2050B16" }
        }
    }

    Item {
        id: heroDeck
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: bottomActionDock.top
        anchors.bottomMargin: 12

        Column {
            id: heroContent
            anchors.left: parent.left
            anchors.leftMargin: 38
            anchors.top: parent.top
            anchors.topMargin: 34
            width: Math.min(parent.width * 0.56, 610)
            spacing: 12

            Row {
                spacing: 12

                Rectangle {
                    width: 32
                    height: 2
                    anchors.verticalCenter: parent.verticalCenter
                    color: Theme.workspaceCyan
                }

                Text {
                    text: "A U T O M A T I O N   R E A D Y"
                    color: Theme.workspaceCyan
                    font.pixelSize: 10
                    font.weight: Font.Bold
                    font.letterSpacing: 2
                }
            }

            Column {
                spacing: -5

                Text {
                    text: "今晚，让电脑"
                    color: Theme.workspaceInk
                    font.pixelSize: 38
                    font.weight: Font.Black
                }

                Text {
                    text: "替你完成收尾。"
                    color: Theme.workspaceAccent
                    font.pixelSize: 38
                    font.weight: Font.Black
                }
            }

            Text {
                width: Math.min(parent.width, 560)
                text: "主画面只保留下一步需要的决定：安排多久、执行什么、现在是否启动。其余高级配置留在精确设定里。"
                color: "#FFC1CDDC"
                font.pixelSize: 12
                lineHeight: 1.45
                wrapMode: Text.WordWrap
            }

            Item { width: 1; height: 4 }

            Row {
                spacing: 18

                Text {
                    id: heroCountdown
                    width: 286
                    text: root.displayedCountdown
                    color: Theme.workspaceInk
                    font.pixelSize: 52
                    font.family: "Consolas"
                    font.weight: Font.Light
                    verticalAlignment: Text.AlignVCenter
                }

                Column {
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 3

                    Text {
                        text: controller.status === "running" ? "距离执行" : "倒计时"
                        color: Theme.workspaceInk
                        font.pixelSize: 13
                        font.weight: Font.Bold
                    }

                    Text {
                        text: "当前动作 · " + controller.actionLabel
                        color: Theme.workspaceMuted
                        font.pixelSize: 10
                    }
                }
            }

            Row {
                id: overviewQuickPresetRow
                spacing: 8

                Repeater {
                    model: [15, 30, 60, 120]

                    NeonButton {
                        required property int modelData
                        compact: true
                        width: 74
                        variant: root.quickMinutes === modelData ? "cyan" : "secondary"
                        text: modelData < 60 ? modelData + " 分钟" : (modelData / 60) + " 小时"
                        onClicked: root.quickMinutes = modelData
                    }
                }

                NeonButton {
                    compact: true
                    width: 74
                    text: "自定义"
                    onClicked: rootWindow.selectWorkspacePage(1)
                }
            }

            Row {
                spacing: 12

                NeonButton {
                    width: 168
                    variant: controller.status === "running" ? "quietDanger" : "primary"
                    leadingIcon: controller.status === "running" ? "■" : "▶"
                    text: controller.status === "running" ? "取消当前任务" : "开始倒计时"
                    onClicked: controller.status === "running"
                               ? controller.cancelCurrentTask()
                               : controller.startQuickCountdown(root.quickMinutes)
                }

                NeonButton {
                    width: 116
                    text: "精确设定"
                    onClicked: rootWindow.selectWorkspacePage(1)
                }

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: controller.status === "running" ? rootWindow.statusLabel() : "预计 " + root.quickMinutes + " 分钟后执行"
                    color: Theme.workspaceMuted
                    font.pixelSize: 10
                }
            }
        }

        Text {
            anchors.left: parent.left
            anchors.leftMargin: 38
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 4
            text: "主操作保持一条直线：选择时长  →  选择动作  →  启动"
            color: "#FF7390AE"
            font.pixelSize: 9
            font.letterSpacing: 0.6
        }

        Item {
            id: characterStage
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: Math.max(380, parent.width * 0.43)
            clip: true

            Rectangle {
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.rightMargin: 34
                anchors.topMargin: 36
                width: Math.min(280, parent.width - 70)
                height: 86
                color: "#D00A1323"
                border.color: "#8058DFF8"
                border.width: 1

                Rectangle {
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: 3
                    color: Theme.workspaceAccent
                }

                Column {
                    anchors.fill: parent
                    anchors.leftMargin: 16
                    anchors.rightMargin: 12
                    anchors.topMargin: 12
                    spacing: 5

                    Text {
                        text: "菲比 · 值守中"
                        color: Theme.workspaceInk
                        font.pixelSize: 13
                        font.weight: Font.Bold
                    }

                    Text {
                        width: parent.width
                        text: controller.status === "running"
                              ? "“任务已经记下啦，接下来交给我吧。”"
                              : "“安心去休息吧，剩下的交给我。”"
                        color: "#FFDCE6F1"
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                    }
                }
            }

            Rectangle {
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.rightMargin: 34
                anchors.topMargin: 36
                width: 42
                height: 1
                color: Theme.workspaceCyan
            }

            Image {
                anchors.right: parent.right
                anchors.rightMargin: 52
                anchors.bottom: parent.bottom
                anchors.bottomMargin: -8
                width: Math.min(275, parent.width * 0.62)
                height: width * 1.258
                source: "../assets/feibi/cutout/base_front.png"
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
            }

            Rectangle {
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.rightMargin: 28
                width: 1
                height: parent.height * 0.72
                color: "#70FF6FAE"
            }
        }
    }

    Rectangle {
        id: bottomActionDock
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: 20
        anchors.rightMargin: 20
        anchors.bottomMargin: 16
        height: 146
        color: "#F20A1424"
        border.color: Theme.workspaceBorder
        border.width: 1

        RowLayout {
            anchors.fill: parent
            spacing: 0

            Item {
                Layout.preferredWidth: 166
                Layout.fillHeight: true

                Rectangle {
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: 1
                    color: Theme.workspaceBorder
                }

                Column {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 18
                    spacing: 7

                    Text {
                        text: "当前任务"
                        color: Theme.workspaceSuccess
                        font.pixelSize: 10
                        font.weight: Font.Bold
                    }

                    Text {
                        width: parent.width
                        text: controller.dashboardTaskTitleText
                        color: Theme.workspaceInk
                        font.pixelSize: 20
                        font.weight: Font.Bold
                        elide: Text.ElideRight
                    }

                    Text {
                        width: parent.width
                        text: controller.dashboardTaskDetailText
                        color: Theme.workspaceMuted
                        font.pixelSize: 9
                        wrapMode: Text.WordWrap
                        maximumLineCount: 2
                        elide: Text.ElideRight
                    }
                }

                NeonButton {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.leftMargin: 18
                    anchors.rightMargin: 18
                    anchors.bottomMargin: 14
                    compact: true
                    variant: "quietDanger"
                    text: "立即执行"
                    enabled: !controller.powerActionInProgress
                    onClicked: rootWindow.requestImmediateExecution()
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                Layout.topMargin: 12
                Layout.bottomMargin: 12
                spacing: 8

                RowLayout {
                    Layout.fillWidth: true

                    Text {
                        text: "执行动作"
                        color: Theme.workspaceInk
                        font.pixelSize: 13
                        font.weight: Font.Bold
                    }

                    Item { Layout.fillWidth: true }

                    Text {
                        text: "当前 · " + controller.actionLabel
                        color: Theme.workspaceSuccess
                        font.pixelSize: 9
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 8

                    ActionTile { Layout.fillWidth: true; actionKey: "shutdown"; actionLabel: "关机"; actionSub: "默认动作" }
                    ActionTile { Layout.fillWidth: true; actionKey: "sleep"; actionLabel: "睡眠"; actionSub: "短暂离开" }
                    ActionTile { Layout.fillWidth: true; actionKey: "hibernate"; actionLabel: "休眠"; actionSub: "保存会话" }
                    ActionTile { Layout.fillWidth: true; actionKey: "restart"; actionLabel: "重启"; actionSub: "刷新系统" }
                    ActionTile { Layout.fillWidth: true; actionKey: "logoff"; actionLabel: "注销"; actionSub: "退出账户" }
                    ActionTile { Layout.fillWidth: true; actionKey: "lock"; actionLabel: "锁定"; actionSub: "锁定屏幕" }
                }
            }

            Item {
                Layout.preferredWidth: 200
                Layout.fillHeight: true

                Rectangle {
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: 1
                    color: Theme.workspaceBorder
                }

                ColumnLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 18
                    anchors.rightMargin: 18
                    anchors.topMargin: 13
                    anchors.bottomMargin: 16
                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true

                        Text {
                            text: "待执行队列"
                            color: Theme.workspaceMuted
                            font.pixelSize: 11
                        }

                        Item { Layout.fillWidth: true }

                        Text {
                            text: controller.queueTaskCount + " 项"
                            color: Theme.workspaceSuccess
                            font.pixelSize: 11
                            font.weight: Font.Bold
                        }
                    }

                    Item { Layout.fillHeight: true }

                    NeonButton {
                        Layout.fillWidth: true
                        variant: "secondary"
                        text: "打开任务中心  ›"
                        onClicked: rootWindow.selectWorkspacePage(2)
                    }
                }
            }
        }
    }
}
