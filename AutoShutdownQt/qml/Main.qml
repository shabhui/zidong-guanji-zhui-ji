import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Window {
    id: mainWindow
    width: 1120
    height: 720
    minimumWidth: 1040
    minimumHeight: 680
    visible: true
    title: "AutoShutdown v2.0-preview"
    color: Theme.bgDeep
    flags: Qt.Window | Qt.FramelessWindowHint

    property int currentPage: 0
    readonly property int topBarHeight: 58
    readonly property int sidebarWidth: 224
    readonly property int outerMargin: 22
    readonly property var pages: ["总览", "定时", "动作", "触发器", "设置"]

    function statusLabel() {
        if (controller.status === "running") return "RUNNING"
        if (controller.status === "paused") return "PAUSED"
        return "READY"
    }

    function safeInt(value, fallback) {
        var parsed = parseInt(value)
        return isNaN(parsed) ? fallback : parsed
    }

    Rectangle {
        anchors.fill: parent
        color: Theme.bgDeep
    }

    // Controlled neon background: subtle, fixed, non-interactive.
    Rectangle {
        width: 430
        height: 430
        radius: 215
        x: -160
        y: -170
        color: Theme.secondary
        opacity: 0.12
    }
    Rectangle {
        width: 360
        height: 360
        radius: 180
        x: parent.width - 230
        y: 58
        color: Theme.primary
        opacity: 0.10
    }
    Rectangle {
        width: 380
        height: 380
        radius: 190
        x: parent.width - 260
        y: parent.height - 220
        color: Theme.accent
        opacity: 0.08
    }

    // Title bar
    Rectangle {
        id: titleBar
        height: topBarHeight
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        color: "#10182B"
        border.color: Theme.borderSoft
        border.width: 1

        MouseArea {
            anchors.fill: parent
            property point lastPos: Qt.point(0, 0)
            onPressed: lastPos = Qt.point(mouse.x, mouse.y)
            onPositionChanged: {
                mainWindow.x += mouse.x - lastPos.x
                mainWindow.y += mouse.y - lastPos.y
            }
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: outerMargin
            anchors.rightMargin: 10
            spacing: 12

            Rectangle {
                Layout.preferredWidth: 38
                Layout.preferredHeight: 38
                radius: 14
                color: Theme.surfaceStrong
                border.color: Theme.borderStrong
                border.width: 1
                Text {
                    anchors.centerIn: parent
                    text: "⏻"
                    color: Theme.primary
                    font.pixelSize: 18
                    font.weight: Font.Bold
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0
                Text {
                    text: "AutoShutdown"
                    color: Theme.textPrimary
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                }
                Text {
                    text: "v2.0-preview · Fluent Neon Control Deck"
                    color: Theme.textSecondary
                    font.pixelSize: 12
                }
            }

            Rectangle {
                Layout.preferredWidth: statusText.implicitWidth + 26
                Layout.preferredHeight: 30
                radius: 15
                color: Theme.surfaceStrong
                border.color: controller.statusColor
                border.width: 1
                Text {
                    id: statusText
                    anchors.centerIn: parent
                    text: mainWindow.statusLabel()
                    color: controller.statusColor
                    font.pixelSize: 12
                    font.weight: Font.Bold
                }
            }

            Button {
                Layout.preferredWidth: 38
                Layout.preferredHeight: 32
                text: "—"
                onClicked: mainWindow.showMinimized()
            }
            Button {
                Layout.preferredWidth: 38
                Layout.preferredHeight: 32
                text: "×"
                onClicked: Qt.quit()
            }
        }
    }

    // Sidebar
    NeonCard {
        id: sidebar
        x: outerMargin
        y: topBarHeight + outerMargin
        width: sidebarWidth
        height: parent.height - topBarHeight - outerMargin * 2
        cardColor: "#2022334A"
        cardBorderColor: Theme.borderSoft
        radius: Theme.radiusXl

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 18
            spacing: 10

            Text {
                text: "NAVIGATION"
                color: Theme.primary
                font.pixelSize: 11
                font.weight: Font.Bold
                font.letterSpacing: 1.4
            }

            Repeater {
                model: pages
                delegate: Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 48
                    radius: Theme.radiusMd
                    color: currentPage === index ? Theme.surfaceStrong : "transparent"
                    border.color: currentPage === index ? Theme.borderStrong : "transparent"
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 14
                        anchors.rightMargin: 14
                        spacing: 10

                        Rectangle {
                            Layout.preferredWidth: 3
                            Layout.preferredHeight: 24
                            radius: 2
                            color: currentPage === index ? Theme.accent : "transparent"
                        }
                        Text {
                            Layout.fillWidth: true
                            text: modelData
                            color: currentPage === index ? Theme.textPrimary : Theme.textSecondary
                            font.pixelSize: 14
                            font.weight: currentPage === index ? Font.Bold : Font.Normal
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: currentPage = index
                    }
                }
            }

            Item { Layout.fillHeight: true }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 104
                radius: Theme.radiusLg
                color: "#20FFFFFF"
                border.color: Theme.borderSoft
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 4
                    Text { text: "安全模式"; color: Theme.textSecondary; font.pixelSize: 12 }
                    Text {
                        text: controller.dryRun ? "Dry-run 已开启" : "真实执行模式"
                        color: controller.dryRun ? Theme.success : Theme.danger
                        font.pixelSize: 15
                        font.weight: Font.Bold
                    }
                    Text {
                        text: "验证时不会真实关机"
                        color: Theme.textSecondary
                        font.pixelSize: 11
                    }
                }
            }
        }
    }

    Item {
        id: contentHost
        x: outerMargin + sidebarWidth + 20
        y: topBarHeight + outerMargin
        width: parent.width - x - outerMargin
        height: parent.height - y - outerMargin

        // Overview page
        Item {
            anchors.fill: parent
            visible: currentPage === 0

            ColumnLayout {
                anchors.fill: parent
                spacing: 16

                NeonCard {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 292
                    cardColor: "#2BFFFFFF"
                    cardBorderColor: Theme.borderStrong
                    radius: Theme.radiusXl

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 26
                        spacing: 24

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 10

                            Rectangle {
                                Layout.preferredWidth: heroPill.implicitWidth + 26
                                Layout.preferredHeight: 30
                                radius: 15
                                color: Theme.surfaceStrong
                                border.color: controller.statusColor
                                border.width: 1
                                Text {
                                    id: heroPill
                                    anchors.centerIn: parent
                                    text: mainWindow.statusLabel()
                                    color: controller.statusColor
                                    font.pixelSize: 12
                                    font.weight: Font.Bold
                                }
                            }

                            Text {
                                text: controller.actionLabel
                                color: Theme.textPrimary
                                font.pixelSize: 30
                                font.weight: Font.Bold
                            }

                            Text {
                                text: controller.remainingText
                                color: controller.status === "running" ? Theme.warning : Theme.textPrimary
                                font.pixelSize: 70
                                font.weight: Font.Bold
                                font.family: "Consolas"
                            }

                            Text {
                                text: controller.targetInfo ? "目标：" + controller.targetInfo : "选择动作和时间，然后启动任务"
                                color: Theme.textSecondary
                                font.pixelSize: 14
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                        }

                        ColumnLayout {
                            Layout.preferredWidth: 230
                            spacing: 12
                            Button {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 42
                                text: "启动 30 分钟倒计时"
                                onClicked: controller.startCountdown(0, 30, 0)
                            }
                            Button {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 42
                                text: "立即执行当前动作"
                                onClicked: confirmDialog.open()
                            }
                            Button {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 42
                                text: "取消任务"
                                enabled: controller.status === "running"
                                onClicked: controller.cancel()
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 162
                    spacing: 16

                    NeonCard {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        cardColor: "#22FFFFFF"
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 18
                            spacing: 12
                            Text { text: "快捷倒计时"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                Button { Layout.fillWidth: true; text: "15 分钟"; onClicked: controller.startCountdown(0, 15, 0) }
                                Button { Layout.fillWidth: true; text: "30 分钟"; onClicked: controller.startCountdown(0, 30, 0) }
                                Button { Layout.fillWidth: true; text: "1 小时"; onClicked: controller.startCountdown(1, 0, 0) }
                                Button { Layout.fillWidth: true; text: "2 小时"; onClicked: controller.startCountdown(2, 0, 0) }
                            }
                        }
                    }

                    NeonCard {
                        Layout.preferredWidth: 300
                        Layout.fillHeight: true
                        cardColor: "#22FFFFFF"
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 18
                            spacing: 7
                            Text { text: "当前配置"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
                            Text { text: "动作：" + controller.actionLabel; color: Theme.textSecondary; font.pixelSize: 13 }
                            Text { text: "强制关闭：" + (controller.forceClose ? "开启" : "关闭"); color: Theme.textSecondary; font.pixelSize: 13 }
                            Text { text: "执行模式：" + (controller.dryRun ? "Dry-run" : "真实执行"); color: controller.dryRun ? Theme.success : Theme.danger; font.pixelSize: 13 }
                        }
                    }
                }

                NeonCard {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    cardColor: "#22FFFFFF"
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 12
                        Text { text: "电源动作"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
                        GridLayout {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            columns: 3
                            rowSpacing: 10
                            columnSpacing: 10
                            ActionTile { Layout.fillWidth: true; actionKey: "shutdown"; actionLabel: "关机"; actionSub: "SHUTDOWN" }
                            ActionTile { Layout.fillWidth: true; actionKey: "sleep"; actionLabel: "睡眠"; actionSub: "SLEEP" }
                            ActionTile { Layout.fillWidth: true; actionKey: "hibernate"; actionLabel: "休眠"; actionSub: "HIBERNATE" }
                            ActionTile { Layout.fillWidth: true; actionKey: "restart"; actionLabel: "重启"; actionSub: "RESTART" }
                            ActionTile { Layout.fillWidth: true; actionKey: "logoff"; actionLabel: "注销"; actionSub: "LOG OUT" }
                            ActionTile { Layout.fillWidth: true; actionKey: "lock"; actionLabel: "锁定"; actionSub: "LOCK" }
                        }
                    }
                }
            }
        }

        // Timer page
        Item {
            anchors.fill: parent
            visible: currentPage === 1

            RowLayout {
                anchors.fill: parent
                spacing: 16

                NeonCard {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    cardColor: "#22FFFFFF"
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 24
                        spacing: 18
                        Text { text: "倒计时"; color: Theme.textPrimary; font.pixelSize: 26; font.weight: Font.Bold }
                        TimeInputPanel { id: countdownInput; Layout.fillWidth: true; Layout.preferredHeight: 126 }
                        Button {
                            Layout.preferredWidth: 180
                            Layout.preferredHeight: 42
                            text: "启动倒计时"
                            onClicked: controller.startCountdown(mainWindow.safeInt(countdownInput.hours, 0), mainWindow.safeInt(countdownInput.minutes, 0), mainWindow.safeInt(countdownInput.seconds, 0))
                        }
                    }
                }

                NeonCard {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    cardColor: "#22FFFFFF"
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 24
                        spacing: 18
                        Text { text: "指定时间"; color: Theme.textPrimary; font.pixelSize: 26; font.weight: Font.Bold }
                        TimeInputPanel { id: fixedInput; Layout.fillWidth: true; Layout.preferredHeight: 126; showSeconds: false; hours: "23"; minutes: "00" }
                        Button {
                            Layout.preferredWidth: 180
                            Layout.preferredHeight: 42
                            text: "启动定时"
                            onClicked: controller.startFixedTime(mainWindow.safeInt(fixedInput.hours, 23), mainWindow.safeInt(fixedInput.minutes, 0))
                        }
                        Text { text: "如果时间已过，会自动排到明天。"; color: Theme.textSecondary; font.pixelSize: 13 }
                    }
                }
            }
        }

        // Actions page
        Item {
            anchors.fill: parent
            visible: currentPage === 2

            NeonCard {
                anchors.fill: parent
                cardColor: "#22FFFFFF"
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 24
                    spacing: 16
                    Text { text: "动作选择"; color: Theme.textPrimary; font.pixelSize: 26; font.weight: Font.Bold }
                    GridLayout {
                        Layout.fillWidth: true
                        columns: 3
                        rowSpacing: 12
                        columnSpacing: 12
                        ActionTile { Layout.fillWidth: true; actionKey: "shutdown"; actionLabel: "关机"; actionSub: "SHUTDOWN" }
                        ActionTile { Layout.fillWidth: true; actionKey: "sleep"; actionLabel: "睡眠"; actionSub: "SLEEP" }
                        ActionTile { Layout.fillWidth: true; actionKey: "hibernate"; actionLabel: "休眠"; actionSub: "HIBERNATE" }
                        ActionTile { Layout.fillWidth: true; actionKey: "restart"; actionLabel: "重启"; actionSub: "RESTART" }
                        ActionTile { Layout.fillWidth: true; actionKey: "logoff"; actionLabel: "注销"; actionSub: "LOG OUT" }
                        ActionTile { Layout.fillWidth: true; actionKey: "lock"; actionLabel: "锁定"; actionSub: "LOCK" }
                    }
                    RowLayout {
                        spacing: 12
                        Button { text: "立即执行当前动作"; onClicked: confirmDialog.open() }
                        Button { text: "取消任务"; enabled: controller.status === "running"; onClicked: controller.cancel() }
                    }
                }
            }
        }

        // Triggers placeholder page
        Item {
            anchors.fill: parent
            visible: currentPage === 3

            NeonCard {
                anchors.fill: parent
                cardColor: "#22FFFFFF"
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 24
                    spacing: 14
                    Text { text: "智能触发"; color: Theme.textPrimary; font.pixelSize: 26; font.weight: Font.Bold }
                    Text {
                        Layout.fillWidth: true
                        text: "v2.0-preview 先聚焦核心倒计时、指定时间和动作执行。网络闲置、进程退出、任务中心等高级能力会在后续预览版迁移。"
                        color: Theme.textSecondary
                        font.pixelSize: 14
                        wrapMode: Text.WordWrap
                    }
                    Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.borderSoft }
                    Text { text: "保留路线：复用 WPF 版已验证的业务规则，再做 QML 高级触发器页面。"; color: Theme.primary; font.pixelSize: 14; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                }
            }
        }

        // Settings page
        Item {
            anchors.fill: parent
            visible: currentPage === 4

            NeonCard {
                anchors.fill: parent
                cardColor: "#22FFFFFF"
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 24
                    spacing: 18
                    Text { text: "设置"; color: Theme.textPrimary; font.pixelSize: 26; font.weight: Font.Bold }
                    RowLayout {
                        Layout.fillWidth: true
                        Text { Layout.fillWidth: true; text: "Dry-run 安全验证"; color: Theme.textPrimary; font.pixelSize: 16; font.weight: Font.Bold }
                        FluentSwitch { checked: controller.dryRun; onCheckedChanged: controller.dryRun = checked }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Text { Layout.fillWidth: true; text: "强制关闭应用"; color: Theme.textPrimary; font.pixelSize: 16; font.weight: Font.Bold }
                        FluentSwitch { checked: controller.forceClose; onCheckedChanged: controller.forceClose = checked }
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "建议验证时保持 Dry-run 开启。关闭后会执行真实系统动作，危险动作仍会弹窗确认。"
                        color: Theme.danger
                        font.pixelSize: 13
                        wrapMode: Text.WordWrap
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
