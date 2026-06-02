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
    title: "AutoShutdown v2.0"
    color: Theme.bgDeep
    flags: Qt.Window | Qt.FramelessWindowHint

    property int currentPage: 0
    readonly property int topBarHeight: 58
    readonly property int sidebarWidth: 224
    readonly property int outerMargin: 22
    readonly property var pages: ["总览", "定时", "任务", "智能触发", "脚本", "设置"]

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
        gradient: Gradient {
            GradientStop { position: 0.0; color: Theme.e5BgA }
            GradientStop { position: 0.46; color: Theme.e5BgB }
            GradientStop { position: 1.0; color: Theme.e5BgC }
        }
    }

    // Starry anime glass background: soft floating orbs and subtle sparkles.
    Rectangle {
        id: orbPurple
        width: 430
        height: 430
        radius: 215
        x: -155
        y: -170
        color: Theme.e5Purple
        opacity: 0.16
        SequentialAnimation on y {
            loops: Animation.Infinite
            NumberAnimation { from: -170; to: -120; duration: Theme.floatVerySlow; easing.type: Easing.InOutSine }
            NumberAnimation { from: -120; to: -170; duration: Theme.floatVerySlow; easing.type: Easing.InOutSine }
        }
        SequentialAnimation on x {
            loops: Animation.Infinite
            NumberAnimation { from: -155; to: -105; duration: Theme.floatVerySlow + 1400; easing.type: Easing.InOutSine }
            NumberAnimation { from: -105; to: -155; duration: Theme.floatVerySlow + 1400; easing.type: Easing.InOutSine }
        }
    }
    Rectangle {
        id: orbCyan
        width: 360
        height: 360
        radius: 180
        x: parent.width - 230
        y: 58
        color: Theme.e5Blue
        opacity: 0.14
        SequentialAnimation on y {
            loops: Animation.Infinite
            NumberAnimation { from: 58; to: 105; duration: Theme.floatVerySlow + 900; easing.type: Easing.InOutSine }
            NumberAnimation { from: 105; to: 58; duration: Theme.floatVerySlow + 900; easing.type: Easing.InOutSine }
        }
    }
    Rectangle {
        id: orbPink
        width: 380
        height: 380
        radius: 190
        x: parent.width - 260
        y: parent.height - 220
        color: Theme.e5Pink
        opacity: 0.12
        SequentialAnimation on x {
            loops: Animation.Infinite
            NumberAnimation { from: mainWindow.width - 260; to: mainWindow.width - 310; duration: Theme.floatVerySlow + 1800; easing.type: Easing.InOutSine }
            NumberAnimation { from: mainWindow.width - 310; to: mainWindow.width - 260; duration: Theme.floatVerySlow + 1800; easing.type: Easing.InOutSine }
        }
    }
    Rectangle {
        id: orbViolet
        width: 260
        height: 260
        radius: 130
        x: 360
        y: parent.height - 150
        color: Theme.e5Purple
        opacity: 0.08
        SequentialAnimation on y {
            loops: Animation.Infinite
            NumberAnimation { from: mainWindow.height - 150; to: mainWindow.height - 205; duration: Theme.floatVerySlow + 2200; easing.type: Easing.InOutSine }
            NumberAnimation { from: mainWindow.height - 205; to: mainWindow.height - 150; duration: Theme.floatVerySlow + 2200; easing.type: Easing.InOutSine }
        }
    }

    Repeater {
        model: 42
        Rectangle {
            width: index % 5 === 0 ? 3 : 2
            height: width
            radius: width / 2
            x: (index * 83) % mainWindow.width
            y: 72 + ((index * 47) % (mainWindow.height - 96))
            color: index % 3 === 0 ? Theme.accent : (index % 3 === 1 ? Theme.primary : "#FFFFFF")
            opacity: 0.16
            SequentialAnimation on opacity {
                loops: Animation.Infinite
                PauseAnimation { duration: 80 * index }
                NumberAnimation { from: 0.10; to: 0.58; duration: 900 + index * 14; easing.type: Easing.InOutSine }
                NumberAnimation { from: 0.58; to: 0.10; duration: 1100 + index * 12; easing.type: Easing.InOutSine }
            }
        }
    }

    NeonCard {
        id: appShell
        x: outerMargin - 8
        y: topBarHeight + outerMargin - 8
        width: parent.width - outerMargin * 2 + 16
        height: parent.height - topBarHeight - outerMargin * 2 + 16
        radius: Theme.radiusXl
        cardColor: Theme.shellGlass
        cardBorderColor: Theme.e5BorderSoft
        hoverable: false
        z: 0
    }

    // Title bar
    Rectangle {
        id: titleBar
        height: topBarHeight
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        color: Theme.glassSoft
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
                color: Theme.glassStrong
                border.color: Theme.borderStrong
                border.width: 1
                Text {
                    anchors.centerIn: parent
                    text: "AS"
                    color: Theme.primary
                    font.pixelSize: 14
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
                    text: "v2.0 · Starry Glass"
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

            Rectangle {
                Layout.preferredWidth: dryRunText.implicitWidth + 24
                Layout.preferredHeight: 30
                radius: 15
                color: controller.dryRun ? "#2262F6B5" : "#22FF5C8A"
                border.color: controller.dryRun ? Theme.success : Theme.danger
                border.width: 1
                Text {
                    id: dryRunText
                    anchors.centerIn: parent
                    text: controller.dryRun ? "DRY RUN" : "LIVE MODE"
                    color: controller.dryRun ? Theme.success : Theme.danger
                    font.pixelSize: 12
                    font.weight: Font.Bold
                }
            }

            NeonButton {
                Layout.preferredWidth: 38
                Layout.preferredHeight: 32
                compact: true
                variant: "ghost"
                text: "—"
                onClicked: mainWindow.showMinimized()
            }
            NeonButton {
                Layout.preferredWidth: 38
                Layout.preferredHeight: 32
                compact: true
                variant: "danger"
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
        z: 1
        cardColor: Theme.shellGlass
        cardBorderColor: Theme.e5BorderSoft
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
                    color: currentPage === index ? Theme.cardGlassActive : "transparent"
                    border.color: currentPage === index ? Theme.e5BorderPink : "transparent"
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
                            color: currentPage === index ? Theme.e5Pink : "transparent"
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
                color: Theme.glassSoft
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
        z: 1

        // Overview page
        Item {
            anchors.fill: parent
            visible: currentPage === 0

            RowLayout {
                anchors.fill: parent
                spacing: 18

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 16

                    NeonCard {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 292
                        cardColor: Theme.cardGlassActive
                        cardBorderColor: Theme.e5BorderPink
                        active: true
                        activeBorderColor: Theme.e5BorderPink
                        radius: Theme.radiusXl
                        breathing: true

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
                                NeonButton {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 44
                                    variant: "primary"
                                    text: "启动倒计时"
                                    onClicked: controller.startCountdown(0, 30, 0)
                                }
                                NeonButton {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 44
                                    variant: "danger"
                                    text: "立即执行当前动作"
                                    onClicked: confirmDialog.open()
                                }
                                NeonButton {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 44
                                    variant: "secondary"
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
                            cardColor: Theme.cardGlass
                            cardBorderColor: Theme.e5BorderSoft
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 18
                                spacing: 12
                                Text { text: "快捷倒计时"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
                                GridLayout {
                                    Layout.fillWidth: true
                                    columns: 2
                                    rowSpacing: 8
                                    columnSpacing: 8

                                    NeonButton {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 38
                                        compact: true
                                        text: "15 分钟"
                                        onClicked: controller.startCountdown(0, 15, 0)
                                    }
                                    NeonButton {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 38
                                        compact: true
                                        text: "30 分钟"
                                        onClicked: controller.startCountdown(0, 30, 0)
                                    }
                                    NeonButton {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 38
                                        compact: true
                                        text: "1 小时"
                                        onClicked: controller.startCountdown(1, 0, 0)
                                    }
                                    NeonButton {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 38
                                        compact: true
                                        text: "2 小时"
                                        onClicked: controller.startCountdown(2, 0, 0)
                                    }
                                }
                            }
                        }

                        NeonCard {
                            Layout.preferredWidth: 300
                            Layout.fillHeight: true
                            cardColor: Theme.cardGlass
                            cardBorderColor: Theme.e5BorderSoft
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
                        cardColor: Theme.cardGlass
                        cardBorderColor: Theme.e5BorderSoft
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

                StarryMascot {
                    Layout.preferredWidth: 286
                    Layout.fillHeight: true
                    title: "星空守夜中"
                    subtitle: controller.dryRun ? "Dry-run safety mode" : "Live power mode enabled"
                }
            }
        }

        // Timer page (1 定时)
        Item {
            anchors.fill: parent
            visible: currentPage === 1

            RowLayout {
                anchors.fill: parent
                spacing: 16

                NeonCard {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    cardColor: Theme.cardGlass
                    cardBorderColor: Theme.e5BorderSoft
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 24
                        spacing: 18
                        Text { text: "倒计时"; color: Theme.textPrimary; font.pixelSize: 26; font.weight: Font.Bold }
                        Text { text: "输入等待时长，启动后按当前电源动作执行。"; color: Theme.textSecondary; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                        TimeInputPanel { id: countdownInput; Layout.fillWidth: true; Layout.preferredHeight: 126 }
                        NeonButton {
                            Layout.preferredWidth: 180
                            Layout.preferredHeight: 44
                            variant: "primary"
                            text: "启动倒计时"
                            onClicked: controller.startCountdown(mainWindow.safeInt(countdownInput.hours, 0), mainWindow.safeInt(countdownInput.minutes, 0), mainWindow.safeInt(countdownInput.seconds, 0))
                        }
                    }
                }

                NeonCard {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    cardColor: Theme.cardGlass
                    cardBorderColor: Theme.e5BorderSoft
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 24
                        spacing: 18
                        Text { text: "指定时间"; color: Theme.textPrimary; font.pixelSize: 26; font.weight: Font.Bold }
                        Text { text: "设定今天的执行时刻；如果时间已过，会自动排到明天。"; color: Theme.textSecondary; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                        TimeInputPanel { id: fixedInput; Layout.fillWidth: true; Layout.preferredHeight: 126; showSeconds: false; hours: "23"; minutes: "00" }
                        NeonButton {
                            Layout.preferredWidth: 180
                            Layout.preferredHeight: 44
                            variant: "primary"
                            text: "启动定时"
                            onClicked: controller.startFixedTime(mainWindow.safeInt(fixedInput.hours, 23), mainWindow.safeInt(fixedInput.minutes, 0))
                        }
                        Text { text: "Dry-run 开启时只验证流程，不会真实执行系统动作。"; color: Theme.success; font.pixelSize: 13 }
                    }
                }
            }
        }

        // Tasks page (2 任务)
        Item {
            anchors.fill: parent
            visible: currentPage === 2

            NeonCard {
                anchors.fill: parent
                cardColor: Theme.cardGlass
                cardBorderColor: Theme.e5BorderSoft
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 24
                    spacing: 16
                    Text { text: "任务中心"; color: Theme.textPrimary; font.pixelSize: 26; font.weight: Font.Bold }
                    Text {
                        Layout.fillWidth: true
                        text: "v2.0 先保留核心倒计时与动作执行。任务模板会复用旧版已验证规则迁移到 QML。"
                        color: Theme.textSecondary
                        font.pixelSize: 14
                        wrapMode: Text.WordWrap
                    }
                    Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.e5BorderSoft; opacity: 0.62 }
                    Text { text: "临时动作选择"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
                    GridLayout {
                        Layout.fillWidth: true
                        columns: 3
                        rowSpacing: 12
                        columnSpacing: 12
                        ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 82; actionKey: "shutdown"; actionLabel: "关机"; actionSub: "SHUTDOWN" }
                        ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 82; actionKey: "sleep"; actionLabel: "睡眠"; actionSub: "SLEEP" }
                        ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 82; actionKey: "hibernate"; actionLabel: "休眠"; actionSub: "HIBERNATE" }
                        ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 82; actionKey: "restart"; actionLabel: "重启"; actionSub: "RESTART" }
                        ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 82; actionKey: "logoff"; actionLabel: "注销"; actionSub: "LOG OUT" }
                        ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 82; actionKey: "lock"; actionLabel: "锁定"; actionSub: "LOCK" }
                    }
                    RowLayout {
                        spacing: 12
                        NeonButton {
                            Layout.preferredWidth: 180
                            Layout.preferredHeight: 44
                            variant: "danger"
                            text: "立即执行当前动作"
                            onClicked: confirmDialog.open()
                        }
                        NeonButton {
                            Layout.preferredWidth: 128
                            Layout.preferredHeight: 44
                            variant: "secondary"
                            text: "取消任务"
                            enabled: controller.status === "running"
                            onClicked: controller.cancel()
                        }
                    }
                }
            }
        }

        // Smart triggers page (3 智能触发)
        Item {
            anchors.fill: parent
            visible: currentPage === 3

            NeonCard {
                anchors.fill: parent
                cardColor: Theme.cardGlass
                cardBorderColor: Theme.e5BorderSoft
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 24
                    spacing: 14
                    Text { text: "智能触发"; color: Theme.textPrimary; font.pixelSize: 26; font.weight: Font.Bold }
                    NeonCard {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 156
                        cardColor: Theme.cardGlass
                        cardBorderColor: Theme.e5BorderPink
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 18
                            spacing: 8
                            Text { text: "网络闲置触发"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
                            Text { text: "下载/上传速度持续低于阈值后执行当前电源动作。高级逻辑将在后续迁移。"; color: Theme.textSecondary; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                            Text { text: "状态：待迁移"; color: Theme.e5Blue; font.pixelSize: 13; font.weight: Font.Bold }
                        }
                    }
                    NeonCard {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 156
                        cardColor: Theme.cardGlass
                        cardBorderColor: Theme.e5BorderPurple
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 18
                            spacing: 8
                            Text { text: "进程退出触发"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
                            Text { text: "监控程序退出后执行当前电源动作，自动关闭子面板将在后续迁移。"; color: Theme.textSecondary; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                            Text { text: "状态：待迁移"; color: Theme.e5Pink; font.pixelSize: 13; font.weight: Font.Bold }
                        }
                    }
                    Item { Layout.fillHeight: true }
                }
            }
        }

        // Script page (4 脚本)
        Item {
            anchors.fill: parent
            visible: currentPage === 4

            NeonCard {
                anchors.fill: parent
                cardColor: Theme.cardGlass
                cardBorderColor: Theme.e5BorderSoft
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 24
                    spacing: 16
                    Text { text: "执行前脚本"; color: Theme.textPrimary; font.pixelSize: 26; font.weight: Font.Bold }
                    Text {
                        Layout.fillWidth: true
                        text: "脚本路径、启用状态和超时设置将在业务逻辑迁移后接入。当前版本保持 Dry-run 安全验证。"
                        color: Theme.textSecondary
                        font.pixelSize: 14
                        wrapMode: Text.WordWrap
                    }
                    Text { text: "状态：未启用"; color: Theme.warning; font.pixelSize: 14; font.weight: Font.Bold }
                    Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.e5BorderSoft; opacity: 0.62 }
                    Text { text: "后续接入项：脚本路径、启用开关、超时秒数、执行日志。"; color: Theme.primary; font.pixelSize: 14; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Item { Layout.fillHeight: true }
                }
            }
        }

        // Settings page (5 设置)
        Item {
            anchors.fill: parent
            visible: currentPage === 5

            NeonCard {
                anchors.fill: parent
                cardColor: Theme.cardGlass
                cardBorderColor: Theme.e5BorderSoft
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
