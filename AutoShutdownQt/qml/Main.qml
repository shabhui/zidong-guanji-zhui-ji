import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Window {
    id: mainWindow
    width: 1160
    height: 760
    visible: true
    title: "AutoShutdown v2.0-preview"
    color: Theme.bgDeep
    flags: Qt.Window | Qt.FramelessWindowHint

    property int currentPage: 0
    readonly property var pageLabels: ["总览", "定时", "动作", "触发器", "设置"]

    MouseArea {
        id: dragArea
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: titleBar.height
        property point lastPos: Qt.point(0, 0)
        onPressed: lastPos = Qt.point(mouse.x, mouse.y)
        onPositionChanged: {
            mainWindow.x += mouse.x - lastPos.x
            mainWindow.y += mouse.y - lastPos.y
        }
    }

    Rectangle {
        anchors.fill: parent
        color: Theme.bgDeep
    }

    // Neon glow fields
    Rectangle {
        width: 360; height: 360; radius: 180
        x: -120; y: -130
        color: Theme.secondary
        opacity: 0.18
    }
    Rectangle {
        width: 300; height: 300; radius: 150
        x: parent.width - 170; y: 70
        color: Theme.primary
        opacity: 0.14
    }
    Rectangle {
        width: 340; height: 340; radius: 170
        x: parent.width - 220; y: parent.height - 190
        color: Theme.accent
        opacity: 0.12
    }

    Rectangle {
        id: titleBar
        anchors.left: parent.left
        anchors.right: parent.right
        height: 54
        color: Theme.bgPanel
        opacity: 0.94
        border.color: Theme.borderSoft
        border.width: 1

        Row {
            anchors.left: parent.left
            anchors.leftMargin: Theme.spaceLg
            anchors.verticalCenter: parent.verticalCenter
            spacing: Theme.spaceSm

            Text {
                text: "AutoShutdown"
                color: Theme.textPrimary
                font.pixelSize: 18
                font.weight: Font.DemiBold
            }
            Text {
                text: "v2.0-preview"
                color: Theme.primary
                font.pixelSize: 13
                anchors.verticalCenter: parent.verticalCenter
            }
            Rectangle {
                radius: Theme.radiusMd
                color: Theme.surfaceStrong
                border.color: controller.statusColor
                border.width: 1
                width: pillLabel.width + 22
                height: 28
                anchors.verticalCenter: parent.verticalCenter
                Text {
                    id: pillLabel
                    anchors.centerIn: parent
                    text: controller.status === "running" ? "RUNNING" : "READY"
                    color: controller.statusColor
                    font.pixelSize: 12
                    font.weight: Font.Bold
                }
            }
        }

        Row {
            anchors.right: parent.right
            anchors.rightMargin: Theme.spaceSm
            anchors.verticalCenter: parent.verticalCenter
            spacing: 6
            RoundButton {
                text: "—"
                radius: 8
                width: 40; height: 32
                flat: true
                onClicked: mainWindow.showMinimized()
            }
            RoundButton {
                text: "×"
                radius: 8
                width: 40; height: 32
                flat: true
                onClicked: Qt.quit()
            }
        }
    }

    Rectangle {
        id: appShell
        anchors.top: titleBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        color: "transparent"

        Row {
            anchors.fill: parent
            anchors.margins: Theme.spaceLg
            spacing: Theme.spaceLg

            NeonCard {
                id: sidebar
                width: 220
                height: parent.height
                cardColor: "#1F20304A"
                cardBorderColor: Theme.borderSoft

                Column {
                    anchors.fill: parent
                    anchors.margins: Theme.spaceLg
                    spacing: Theme.spaceSm

                    Text {
                        text: "Fluent Neon Rail"
                        color: Theme.primary
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                    }

                    Repeater {
                        model: pageLabels
                        delegate: Item {
                            width: 185
                            height: 46

                            Rectangle {
                                anchors.fill: parent
                                radius: Theme.radiusMd
                                color: mainWindow.currentPage === index ? Theme.surfaceStrong : "transparent"
                                border.color: mainWindow.currentPage === index ? Theme.borderStrong : "transparent"
                                border.width: 1

                                Row {
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.left: parent.left
                                    anchors.leftMargin: Theme.spaceMd
                                    spacing: Theme.spaceSm

                                    Rectangle {
                                        width: 3; height: 22; radius: 2
                                        color: mainWindow.currentPage === index ? Theme.accent : "transparent"
                                    }
                                    Text {
                                        text: modelData
                                        color: mainWindow.currentPage === index ? Theme.textPrimary : Theme.textSecondary
                                        font.pixelSize: 14
                                        font.weight: mainWindow.currentPage === index ? Font.Bold : Font.Normal
                                    }
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: mainWindow.currentPage = index
                            }
                        }
                    }

                    Item { height: 1; width: 1; Layout.fillHeight: true }

                    Rectangle {
                        width: parent.width
                        height: 92
                        radius: Theme.radiusLg
                        color: Theme.surfaceGlass
                        border.color: Theme.borderSoft
                        border.width: 1
                        anchors.bottom: parent.bottom

                        Column {
                            anchors.fill: parent
                            anchors.margins: Theme.spaceMd
                            spacing: 6
                            Text { text: "当前版本"; color: Theme.textSecondary; font.pixelSize: 11 }
                            Text { text: "v2.0-preview"; color: Theme.accent; font.pixelSize: 15; font.weight: Font.Bold }
                            Text { text: controller.dryRun ? "Dry-run 安全模式" : "真实执行模式"; color: controller.dryRun ? Theme.success : Theme.danger; font.pixelSize: 12 }
                        }
                    }
                }
            }

            StackLayout {
                id: pageStack
                width: parent.width - sidebar.width - Theme.spaceLg
                height: parent.height
                currentIndex: mainWindow.currentPage

                // Overview
                Item {
                    Column {
                        anchors.fill: parent
                        spacing: Theme.spaceMd

                        StatusHero { width: parent.width; height: 285 }

                        Row {
                            width: parent.width
                            height: 150
                            spacing: Theme.spaceMd

                            NeonCard {
                                width: (parent.width - Theme.spaceMd) * 0.52
                                height: parent.height
                                cardColor: "#24FFFFFF"
                                Column {
                                    anchors.fill: parent
                                    anchors.margins: Theme.spaceLg
                                    spacing: Theme.spaceMd
                                    Text { text: "快捷倒计时"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
                                    Row {
                                        spacing: Theme.spaceSm
                                        Repeater {
                                            model: [
                                                { label: "15 分钟", seconds: 900 },
                                                { label: "30 分钟", seconds: 1800 },
                                                { label: "1 小时", seconds: 3600 },
                                                { label: "2 小时", seconds: 7200 }
                                            ]
                                            delegate: Button {
                                                text: modelData.label
                                                onClicked: controller.startCountdown(0, Math.floor(modelData.seconds / 60), 0)
                                            }
                                        }
                                    }
                                }
                            }

                            NeonCard {
                                width: (parent.width - Theme.spaceMd) * 0.48
                                height: parent.height
                                cardColor: "#24FFFFFF"
                                Column {
                                    anchors.fill: parent
                                    anchors.margins: Theme.spaceLg
                                    spacing: 8
                                    Text { text: "当前配置"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
                                    Text { text: "动作：" + controller.actionLabel; color: Theme.textSecondary; font.pixelSize: 13 }
                                    Text { text: "强制关闭：" + (controller.forceClose ? "开启" : "关闭"); color: Theme.textSecondary; font.pixelSize: 13 }
                                    Text { text: "执行模式：" + (controller.dryRun ? "Dry-run 安全验证" : "真实执行"); color: controller.dryRun ? Theme.success : Theme.danger; font.pixelSize: 13 }
                                }
                            }
                        }

                        NeonCard {
                            width: parent.width
                            height: 185
                            cardColor: "#24FFFFFF"
                            Column {
                                anchors.fill: parent
                                anchors.margins: Theme.spaceLg
                                spacing: Theme.spaceMd
                                Text { text: "电源动作"; color: Theme.textPrimary; font.pixelSize: 20; font.weight: Font.Bold }
                                Grid {
                                    columns: 3
                                    columnSpacing: Theme.spaceMd
                                    rowSpacing: Theme.spaceMd
                                    ActionTile { actionKey: "shutdown"; actionLabel: "关机"; actionSub: "SHUTDOWN" }
                                    ActionTile { actionKey: "sleep"; actionLabel: "睡眠"; actionSub: "SLEEP" }
                                    ActionTile { actionKey: "hibernate"; actionLabel: "休眠"; actionSub: "HIBERNATE" }
                                    ActionTile { actionKey: "restart"; actionLabel: "重启"; actionSub: "RESTART" }
                                    ActionTile { actionKey: "logoff"; actionLabel: "注销"; actionSub: "LOG OUT" }
                                    ActionTile { actionKey: "lock"; actionLabel: "锁定"; actionSub: "LOCK" }
                                }
                            }
                        }
                    }
                }

                // Timer
                Item {
                    Row {
                        anchors.fill: parent
                        spacing: Theme.spaceMd

                        NeonCard {
                            width: (parent.width - Theme.spaceMd) / 2
                            height: 360
                            cardColor: "#24FFFFFF"
                            Column {
                                anchors.fill: parent
                                anchors.margins: Theme.spaceLg
                                spacing: Theme.spaceMd
                                Text { text: "倒计时"; color: Theme.textPrimary; font.pixelSize: 22; font.weight: Font.Bold }
                                TimeInputPanel { id: countdownInput; width: parent.width; height: 120 }
                                Button {
                                    text: "启动倒计时"
                                    onClicked: controller.startCountdown(parseInt(countdownInput.hours || "0"), parseInt(countdownInput.minutes || "0"), parseInt(countdownInput.seconds || "0"))
                                }
                                Button { text: "取消任务"; onClicked: controller.cancel() }
                            }
                        }

                        NeonCard {
                            width: (parent.width - Theme.spaceMd) / 2
                            height: 360
                            cardColor: "#24FFFFFF"
                            Column {
                                anchors.fill: parent
                                anchors.margins: Theme.spaceLg
                                spacing: Theme.spaceMd
                                Text { text: "指定时间"; color: Theme.textPrimary; font.pixelSize: 22; font.weight: Font.Bold }
                                TimeInputPanel { id: fixedInput; width: parent.width; height: 120; showSeconds: false; hours: "23"; minutes: "00" }
                                Button {
                                    text: "启动定时"
                                    onClicked: controller.startFixedTime(parseInt(fixedInput.hours || "0"), parseInt(fixedInput.minutes || "0"))
                                }
                                Text { text: "如果时间已过，将自动排到明天。"; color: Theme.textSecondary; font.pixelSize: 13 }
                            }
                        }
                    }
                }

                // Actions
                Item {
                    Column {
                        anchors.fill: parent
                        spacing: Theme.spaceMd
                        Text { text: "动作选择"; color: Theme.textPrimary; font.pixelSize: 26; font.weight: Font.Bold }
                        Grid {
                            columns: 3
                            columnSpacing: Theme.spaceMd
                            rowSpacing: Theme.spaceMd
                            ActionTile { actionKey: "shutdown"; actionLabel: "关机"; actionSub: "SHUTDOWN" }
                            ActionTile { actionKey: "sleep"; actionLabel: "睡眠"; actionSub: "SLEEP" }
                            ActionTile { actionKey: "hibernate"; actionLabel: "休眠"; actionSub: "HIBERNATE" }
                            ActionTile { actionKey: "restart"; actionLabel: "重启"; actionSub: "RESTART" }
                            ActionTile { actionKey: "logoff"; actionLabel: "注销"; actionSub: "LOG OUT" }
                            ActionTile { actionKey: "lock"; actionLabel: "锁定"; actionSub: "LOCK" }
                        }
                        Row {
                            spacing: Theme.spaceMd
                            Button { text: "立即执行当前动作"; onClicked: confirmDialog.open() }
                            Button { text: "取消当前任务"; onClicked: controller.cancel() }
                        }
                    }
                }

                // Triggers preview
                Item {
                    Column {
                        anchors.fill: parent
                        spacing: Theme.spaceMd
                        Text { text: "智能触发（后续迁移）"; color: Theme.textPrimary; font.pixelSize: 26; font.weight: Font.Bold }
                        NeonCard {
                            width: parent.width
                            height: 130
                            cardColor: "#22FFFFFF"
                            Column {
                                anchors.fill: parent
                                anchors.margins: Theme.spaceLg
                                spacing: 8
                                Text { text: "网络闲置触发"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
                                Text { text: "v2.0-preview 先聚焦核心倒计时与动作执行，高级触发器将在后续预览版迁移。"; color: Theme.textSecondary; font.pixelSize: 14; wrapMode: Text.WordWrap; width: parent.width }
                            }
                        }
                        NeonCard {
                            width: parent.width
                            height: 130
                            cardColor: "#22FFFFFF"
                            Column {
                                anchors.fill: parent
                                anchors.margins: Theme.spaceLg
                                spacing: 8
                                Text { text: "进程退出触发"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
                                Text { text: "功能入口保留，正式迁移时会复用 WPF 版已验证的业务规则。"; color: Theme.textSecondary; font.pixelSize: 14; wrapMode: Text.WordWrap; width: parent.width }
                            }
                        }
                    }
                }

                // Settings
                Item {
                    Column {
                        anchors.fill: parent
                        spacing: Theme.spaceMd
                        Text { text: "设置"; color: Theme.textPrimary; font.pixelSize: 26; font.weight: Font.Bold }
                        NeonCard {
                            width: parent.width
                            height: 210
                            cardColor: "#24FFFFFF"
                            Column {
                                anchors.fill: parent
                                anchors.margins: Theme.spaceLg
                                spacing: Theme.spaceMd
                                Row {
                                    width: parent.width
                                    Text { text: "Dry-run 安全验证"; color: Theme.textPrimary; font.pixelSize: 16; font.weight: Font.Bold; width: parent.width - 70 }
                                    FluentSwitch { checked: controller.dryRun; onCheckedChanged: controller.dryRun = checked }
                                }
                                Row {
                                    width: parent.width
                                    Text { text: "强制关闭应用"; color: Theme.textPrimary; font.pixelSize: 16; font.weight: Font.Bold; width: parent.width - 70 }
                                    FluentSwitch { checked: controller.forceClose; onCheckedChanged: controller.forceClose = checked }
                                }
                                Text { text: "关闭 Dry-run 后会执行真实系统动作，危险动作仍会弹窗确认。"; color: Theme.danger; font.pixelSize: 13; wrapMode: Text.WordWrap; width: parent.width }
                            }
                        }
                    }
                }
            }
        }
    }

    ConfirmDialog {
        id: confirmDialog
        anchors.centerIn: parent
        actionLabel: controller.actionLabel
    }
}
