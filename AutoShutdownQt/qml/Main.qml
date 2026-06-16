import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import "components"

Window {
    id: mainWindow
    width: 1120
    height: 720
    minimumWidth: 1040
    minimumHeight: 680
    visible: true
    title: "定时关机助手 v3.2"
    color: Theme.bgDeep
    flags: Qt.Window | Qt.FramelessWindowHint

    property int currentPage: 0
    property bool dryRunSwitchSyncing: false
    property bool trayCloseRequested: false
    property var queueRowModel: queueRows()
    property var musicTrackModel: musicTracks()
    property var historyRowModel: historyRows()
    readonly property int topBarHeight: 58
    readonly property int navWidth: 208
    readonly property int outerMargin: 20
    readonly property var pageNames: ["总览", "定时", "任务", "智能触发", "脚本", "设置"]

    function statusLabel() {
        if (controller.status === "running") return "运行中"
        if (controller.status === "paused") return "已暂停"
        return "就绪"
    }

    function safeInt(value, fallback) {
        var parsed = parseInt(value)
        return isNaN(parsed) ? fallback : parsed
    }

    function safeFloat(value, fallback) {
        var parsed = parseFloat(value)
        return isNaN(parsed) ? fallback : parsed
    }

    function queueRows() {
        try {
            return JSON.parse(controller.queueRowsJson)
        } catch (error) {
            return []
        }
    }

    function musicTracks() {
        try {
            return JSON.parse(controller.musicTracksJson)
        } catch (error) {
            return []
        }
    }

    function historyRows() {
        try {
            return JSON.parse(controller.historyRowsJson)
        } catch (error) {
            return []
        }
    }

    function toggleMaximized() {
        if (mainWindow.visibility === Window.Maximized) {
            mainWindow.showNormal()
        } else {
            mainWindow.showMaximized()
        }
    }

    function formatLogCategorySummary(summary) {
        var text = String(summary || "")
        var info = (text.match(/信息=(\d+)/) || ["", "0"])[1]
        var warning = (text.match(/警告=(\d+)/) || ["", "0"])[1]
        var error = (text.match(/错误=(\d+)/) || ["", "0"])[1]
        return "日志分类：信息 " + info + " · 警告 " + warning + " · 错误 " + error
    }

    function formatPowerActionStepSummary(summary) {
        var text = String(summary || "")
        if (text === "") {
            return "执行阶段：就绪 · 脚本预检：等待 · 关闭应用：等待 · 系统动作：等待"
        }
        return text
    }

    function syncDryRunSwitchState() {
        if (dryRunSafetySwitch.checked !== controller.dryRun) {
            dryRunSwitchSyncing = true
            dryRunSafetySwitch.checked = controller.dryRun
            dryRunSwitchSyncing = false
        }
    }

    function confirmLiveModeFromSwitch(checked) {
        if (dryRunSwitchSyncing || checked === controller.dryRun) {
            return
        }
        if (checked) {
            controller.requestDryRunChange(true)
            return
        }
        mainWindow.syncDryRunSwitchState()
        liveModeConfirmDialog.open()
    }

    Connections {
        target: controller
        function onDryRunChanged() {
            mainWindow.syncDryRunSwitchState()
        }
        function onTaskQueueChanged() {
            mainWindow.queueRowModel = mainWindow.queueRows()
        }
        function onMusicChanged() {
            mainWindow.musicTrackModel = mainWindow.musicTracks()
        }
        function onReminderChanged() {
            if (controller.reminderDialogTitle !== "") {
                reminderDialog.open()
            }
        }
        function onHistoryChanged() {
            mainWindow.historyRowModel = mainWindow.historyRows()
        }
    }

    Component.onCompleted: {
        if (!controller.firstRunSafetyGuideShown) {
            firstRunSafetyGuideDialog.open()
        }
    }

    onClosing: function(close) {
        if (controller.trayAvailable && !trayCloseRequested) {
            close.accepted = false
            if (!controller.trayCloseHintShown) {
                trayCloseHintDialog.open()
            } else {
                controller.minimizeToTray()
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: Theme.e5BgA }
            GradientStop { position: 0.46; color: Theme.e5BgB }
            GradientStop { position: 1.0; color: Theme.e5BgC }
        }
    }

    // Quiet depth layers behind the work surface.
    Rectangle {
        id: panelWashTop
        x: outerMargin
        y: topBarHeight + 20
        width: parent.width - outerMargin * 2
        height: 178
        radius: Theme.radiusXl
        color: Theme.e5Blue
        opacity: 0.024
    }
    Rectangle {
        id: panelWashBottom
        x: outerMargin + navWidth + 20
        y: parent.height - 190
        width: parent.width - x - outerMargin
        height: 142
        radius: Theme.radiusXl
        color: Theme.primary
        opacity: 0.028
    }

    NeonCard {
        id: appShell
        x: outerMargin - 8
        y: topBarHeight + outerMargin - 8
        width: parent.width - outerMargin * 2 + 16
        height: parent.height - topBarHeight - outerMargin * 2 + 16
        radius: Theme.radiusXl
        cardColor: Theme.dialogPanel
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
        color: Theme.dialogPanel
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
            onDoubleClicked: mainWindow.toggleMaximized()
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: outerMargin
            anchors.rightMargin: 10
            spacing: 10

            Rectangle {
                Layout.preferredWidth: 38
                Layout.preferredHeight: 38
                radius: 14
                color: Theme.glassStrong
                border.color: Theme.borderStrong
                border.width: 1
                Image {
                    anchors.fill: parent
                    anchors.margins: 3
                    source: "../app_icon.png"
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0
                Text {
                    text: "定时关机助手"
                    color: Theme.textPrimary
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                }
                Text {
                    text: "v3.2 · 安静工作台"
                    color: Theme.textSecondary
                    font.pixelSize: 12
                }
            }

            Rectangle {
                Layout.preferredWidth: statusText.implicitWidth + 24
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
                Layout.preferredWidth: dryRunText.implicitWidth + 22
                Layout.preferredHeight: 30
                radius: 15
                color: controller.dryRun ? "#2262F6B5" : "#22FF5C8A"
                border.color: controller.dryRun ? Theme.success : Theme.danger
                border.width: 1
                Text {
                    id: dryRunText
                    anchors.centerIn: parent
                    text: controller.dryRun ? "安全验证" : "真实执行"
                    color: controller.dryRun ? Theme.success : Theme.danger
                    font.pixelSize: 12
                    font.weight: Font.Bold
                }
            }

            NeonButton {
                Layout.preferredWidth: 88
                Layout.preferredHeight: 32
                compact: true
                variant: "ghost"
                text: "音乐"
                ToolTip.visible: hovered
                ToolTip.delay: 400
                ToolTip.text: "打开音乐播放器"
                onClicked: musicPlayerWindow.show()
            }

            NeonButton {
                Layout.preferredWidth: 38
                Layout.preferredHeight: 32
                compact: true
                variant: "ghost"
                text: "—"
                ToolTip.visible: hovered
                ToolTip.delay: 400
                ToolTip.text: "最小化"
                onClicked: mainWindow.showMinimized()
            }
            NeonButton {
                Layout.preferredWidth: 38
                Layout.preferredHeight: 32
                compact: true
                variant: "ghost"
                text: mainWindow.visibility === Window.Maximized ? "❐" : "□"
                ToolTip.visible: hovered
                ToolTip.delay: 400
                ToolTip.text: "最大化/还原"
                onClicked: mainWindow.toggleMaximized()
            }
            NeonButton {
                Layout.preferredWidth: 38
                Layout.preferredHeight: 32
                compact: true
                variant: "danger"
                text: "×"
                ToolTip.visible: hovered
                ToolTip.delay: 400
                ToolTip.text: "关闭到托盘或退出"
                onClicked: mainWindow.close()
            }
        }
    }

    // Sidebar
    NeonCard {
        id: navigationRail
        x: outerMargin
        y: topBarHeight + outerMargin
        width: navWidth
        height: parent.height - topBarHeight - outerMargin * 2
        z: 1
        cardColor: Theme.dialogPanel
        cardBorderColor: Theme.e5BorderSoft
        radius: Theme.radiusXl

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 8

            Text {
                text: "导航"
                color: Theme.primary
                font.pixelSize: 11
                font.weight: Font.Bold
            }

            Repeater {
                model: pageNames
                delegate: Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 46
                    radius: Theme.radiusMd
                    color: currentPage === index ? Theme.cardGlassActive : "transparent"
                    border.color: currentPage === index ? Theme.borderStrong : "transparent"
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 13
                        anchors.rightMargin: 13
                        spacing: 9

                        Rectangle {
                            Layout.preferredWidth: 3
                            Layout.preferredHeight: 24
                            radius: 2
                            color: currentPage === index ? Theme.primary : "transparent"
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
                Layout.preferredHeight: 98
                radius: Theme.radiusLg
                color: Theme.dialogPanelRaised
                border.color: Theme.borderSoft
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 4
                    Text { text: "安全模式"; color: Theme.textSecondary; font.pixelSize: 12 }
                    Text {
                        text: controller.dryRun ? "安全验证已开启" : "真实执行模式"
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
        x: outerMargin + navWidth + 20
        y: topBarHeight + outerMargin
        width: parent.width - x - outerMargin
        height: parent.height - y - outerMargin
        z: 1

        // Overview page
        Item {
            anchors.fill: parent
            visible: currentPage === 0

            Item {
                id: overviewWorkbench
                anchors.fill: parent
                readonly property int overviewGap: 16
                readonly property int overviewRightWidth: 360
                readonly property int overviewLeftWidth: width - overviewRightWidth - overviewGap

                NeonCard {
                    id: currentTaskPanel
                    x: 0
                    y: 0
                    width: overviewWorkbench.overviewLeftWidth
                    height: 318
                    cardColor: Theme.dialogPanelRaised
                    cardBorderColor: Theme.borderStrong
                    activeBorderColor: Theme.borderStrong
                    radius: Theme.radiusXl

                    ColumnLayout {
                        id: currentTaskContent
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 5

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10
                            Rectangle {
                                Layout.preferredWidth: heroPill.implicitWidth + 24
                                Layout.preferredHeight: 28
                                radius: 14
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
                                Layout.fillWidth: true
                                text: controller.actionLabel
                                color: Theme.textPrimary
                                font.pixelSize: 20
                                font.weight: Font.Bold
                                elide: Text.ElideRight
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            text: controller.remainingText
                            color: controller.status === "running" ? Theme.warning : Theme.textPrimary
                            font.pixelSize: 42
                            font.weight: Font.Bold
                            font.family: "Consolas"
                            horizontalAlignment: Text.AlignLeft
                            fontSizeMode: Text.HorizontalFit
                            minimumPixelSize: 32
                            maximumLineCount: 1
                        }

                        Text {
                            Layout.fillWidth: true
                            text: controller.targetInfo ? "目标：" + controller.targetInfo : "选择动作和时间，然后启动任务"
                            color: Theme.textSecondary
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                            maximumLineCount: 2
                        }

                        Text {
                            Layout.fillWidth: true
                            visible: controller.powerActionInProgress
                            text: controller.powerActionProgressText
                            color: Theme.warning
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                            maximumLineCount: 1
                        }

                        Text {
                            Layout.fillWidth: true
                            text: mainWindow.formatPowerActionStepSummary(controller.powerActionStepSummaryText)
                            color: Theme.textSecondary
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                            maximumLineCount: 1
                        }

                        GridLayout {
                            id: currentTaskActions
                            Layout.fillWidth: true
                            columns: 2
                            rowSpacing: 7
                            columnSpacing: 8
                            NeonButton {
                                Layout.fillWidth: true
                                Layout.columnSpan: 2
                                Layout.preferredHeight: 34
                                compact: true
                                variant: "primary"
                                text: "启动 30 分钟倒计时"
                                onClicked: controller.startCountdown(0, 30, 0)
                            }
                            NeonButton {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 30
                                compact: true
                                variant: "secondary"
                                text: "取消任务"
                                enabled: controller.status === "running"
                                onClicked: controller.cancel()
                            }
                            NeonButton {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 30
                                compact: true
                                variant: "secondary"
                                text: "跳过等待"
                                visible: controller.canSkipCloseAppsWait
                                onClicked: controller.skipCloseAppsWait()
                            }
                            NeonButton {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 30
                                compact: true
                                variant: "secondary"
                                text: "延后 5 分钟"
                                enabled: controller.status === "running"
                                onClicked: controller.snoozeMinutes(5)
                            }
                            NeonButton {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 30
                                compact: true
                                variant: "secondary"
                                text: "延后 10 分钟"
                                enabled: controller.status === "running"
                                onClicked: controller.snoozeMinutes(10)
                            }
                            NeonButton {
                                Layout.fillWidth: true
                                Layout.columnSpan: 2
                                Layout.preferredHeight: 28
                                compact: true
                                variant: "quietDanger"
                                text: "立即执行当前动作"
                                enabled: !controller.powerActionInProgress
                                onClicked: confirmDialog.open()
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            visible: !controller.dryRun
                            text: "真实执行模式：请确认未保存工作，当前动作可能影响系统电源状态。"
                            color: Theme.danger
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                            maximumLineCount: 1
                        }
                    }
                }

                NeonCard {
                    id: overviewActionPanel
                    x: 0
                    y: currentTaskPanel.height + overviewWorkbench.overviewGap
                    width: overviewWorkbench.overviewLeftWidth
                    height: parent.height - y
                    cardColor: Theme.dialogPanel
                    cardBorderColor: Theme.e5BorderSoft
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 6
                        Text { text: "电源动作"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
                        GridLayout {
                            Layout.fillWidth: true
                            columns: 3
                            rowSpacing: 6
                            columnSpacing: 8
                            ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 56; actionKey: "shutdown"; actionLabel: "关机"; actionSub: "模拟关机" }
                            ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 56; actionKey: "sleep"; actionLabel: "睡眠"; actionSub: "进入睡眠" }
                            ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 56; actionKey: "hibernate"; actionLabel: "休眠"; actionSub: "进入休眠" }
                            ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 56; actionKey: "restart"; actionLabel: "重启"; actionSub: "重新启动" }
                            ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 56; actionKey: "logoff"; actionLabel: "注销"; actionSub: "退出登录" }
                            ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 56; actionKey: "lock"; actionLabel: "锁定"; actionSub: "锁定屏幕" }
                        }
                    }
                }

                Item {
                    id: rightStatusPanel
                    x: overviewWorkbench.overviewLeftWidth + overviewWorkbench.overviewGap
                    y: 0
                    width: overviewWorkbench.overviewRightWidth
                    height: parent.height

                    NeonCard {
                        id: quickCountdownPanel
                        x: 0
                        y: 0
                        width: parent.width
                        height: 150
                        cardColor: Theme.dialogPanel
                        cardBorderColor: Theme.e5BorderSoft
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 16
                            spacing: 10
                            Text { text: "快捷倒计时"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
                            GridLayout {
                                Layout.fillWidth: true
                                columns: 2
                                rowSpacing: 8
                                columnSpacing: 8
                                NeonButton { Layout.fillWidth: true; Layout.preferredHeight: 38; compact: true; text: "15 分钟"; onClicked: controller.startCountdown(0, 15, 0) }
                                NeonButton { Layout.fillWidth: true; Layout.preferredHeight: 38; compact: true; text: "30 分钟"; onClicked: controller.startCountdown(0, 30, 0) }
                                NeonButton { Layout.fillWidth: true; Layout.preferredHeight: 38; compact: true; text: "1 小时"; onClicked: controller.startCountdown(1, 0, 0) }
                                NeonButton { Layout.fillWidth: true; Layout.preferredHeight: 38; compact: true; text: "2 小时"; onClicked: controller.startCountdown(2, 0, 0) }
                            }
                        }
                    }

                    NeonCard {
                        id: overviewStatusSummary
                        x: 0
                        y: quickCountdownPanel.height + overviewWorkbench.overviewGap
                        width: parent.width
                        height: 226
                        cardColor: Theme.dialogPanel
                        cardBorderColor: Theme.e5BorderSoft
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 16
                            spacing: 8

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                Text { Layout.fillWidth: true; text: "运行概览"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.DemiBold }
                                Text {
                                    text: controller.dryRun ? "安全验证" : "真实执行"
                                    color: controller.dryRun ? Theme.success : Theme.danger
                                    font.pixelSize: 12
                                    font.weight: Font.DemiBold
                                }
                            }

                            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.e5BorderSoft; opacity: 0.42 }

                            GridLayout {
                                Layout.fillWidth: true
                                columns: 2
                                rowSpacing: 7
                                columnSpacing: 12

                                Text { text: "动作"; color: Theme.textSecondary; font.pixelSize: 11 }
                                Text { Layout.fillWidth: true; text: controller.actionLabel; color: Theme.textPrimary; font.pixelSize: 12; font.weight: Font.DemiBold; elide: Text.ElideRight }

                                Text { text: "强制关闭"; color: Theme.textSecondary; font.pixelSize: 11 }
                                Text { text: controller.forceClose ? "开启" : "关闭"; color: Theme.textPrimary; font.pixelSize: 12 }

                                Text { text: "队列"; color: Theme.textSecondary; font.pixelSize: 11 }
                                Text { text: String(mainWindow.queueRowModel.length) + " 个任务"; color: mainWindow.queueRowModel.length > 0 ? Theme.warning : Theme.textSecondary; font.pixelSize: 12; font.weight: Font.DemiBold }

                                Text { text: "触发器"; color: Theme.textSecondary; font.pixelSize: 11 }
                                Text {
                                    Layout.fillWidth: true
                                    text: (controller.processTriggerActive || controller.networkTriggerActive) ? "已启用" : "未启用"
                                    color: (controller.processTriggerActive || controller.networkTriggerActive) ? Theme.warning : Theme.textSecondary
                                    font.pixelSize: 12
                                    font.weight: Font.DemiBold
                                    horizontalAlignment: Text.AlignLeft
                                }
                            }

                            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.e5BorderSoft; opacity: 0.26 }

                            Text {
                                Layout.fillWidth: true
                                text: mainWindow.queueRowModel.length > 0 ? "下一任务：" + mainWindow.queueRowModel[0].name : "下一任务：暂无排队任务"
                                color: Theme.textSecondary
                                font.pixelSize: 11
                                elide: Text.ElideRight
                                maximumLineCount: 1
                            }
                        }
                    }

                    NeonCard {
                        id: overviewRecentActivity
                        x: 0
                        y: overviewStatusSummary.y + overviewStatusSummary.height + overviewWorkbench.overviewGap
                        width: parent.width
                        height: parent.height - y
                        cardColor: Theme.dialogPanel
                        cardBorderColor: Theme.e5BorderSoft
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 16
                            spacing: 8
                            Text { text: "最近活动"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
                            Text { text: "后台托盘"; color: Theme.textSecondary; font.pixelSize: 12; font.weight: Font.Bold }
                            Text { text: "托盘可用时关闭窗口隐藏到后台"; color: Theme.e5Blue; font.pixelSize: 12; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.e5BorderSoft; opacity: 0.55 }
                            Text { Layout.fillWidth: true; Layout.fillHeight: true; text: controller.logText; color: Theme.textSecondary; font.pixelSize: 11; wrapMode: Text.WordWrap; elide: Text.ElideRight }
                        }
                    }
                }
            }
        }

        // Timer page (1 定时)
        Item {
            anchors.fill: parent
            visible: currentPage === 1

            ColumnLayout {
                anchors.fill: parent
                spacing: 14

                NeonCard {
                    id: timerActionContextCard
                    Layout.fillWidth: true
                    Layout.preferredHeight: 76
                    cardColor: Theme.dialogPanelRaised
                    cardBorderColor: Theme.e5BorderSoft
                    hoverable: false

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 16

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Text { text: "执行动作"; color: Theme.textPrimary; font.pixelSize: 16; font.weight: Font.Bold }
                            Text {
                                Layout.fillWidth: true
                                text: "当前动作：" + controller.actionLabel + " · 倒计时和指定时间会按此动作加入任务队列"
                                color: Theme.textSecondary
                                font.pixelSize: 12
                                elide: Text.ElideRight
                                maximumLineCount: 1
                            }
                        }

                        ComboBox {
                            id: timerActionCombo
                            property bool syncing: true
                            Layout.preferredWidth: 150
                            Layout.preferredHeight: 36
                            enabled: !controller.powerActionInProgress
                            model: [
                                { label: "关机", value: "shutdown" },
                                { label: "睡眠", value: "sleep" },
                                { label: "休眠", value: "hibernate" },
                                { label: "重启", value: "restart" },
                                { label: "注销", value: "logoff" },
                                { label: "锁定", value: "lock" }
                            ]
                            textRole: "label"
                            valueRole: "value"

                            function syncFromController() {
                                syncing = true
                                currentIndex = controller.selectedAction === "sleep" ? 1
                                             : controller.selectedAction === "hibernate" ? 2
                                             : controller.selectedAction === "restart" ? 3
                                             : controller.selectedAction === "logoff" ? 4
                                             : controller.selectedAction === "lock" ? 5
                                             : 0
                                syncing = false
                            }

                            contentItem: Text {
                                text: timerActionCombo.displayText
                                color: Theme.textPrimary
                                font.pixelSize: 13
                                verticalAlignment: Text.AlignVCenter
                                leftPadding: 10
                                rightPadding: 26
                                elide: Text.ElideRight
                            }
                            background: Rectangle {
                                color: Theme.inputGlass
                                radius: Theme.radiusSm
                                border.color: timerActionCombo.enabled ? Theme.e5BorderSoft : Theme.borderSoft
                                border.width: 1
                            }
                            onCurrentValueChanged: if (!syncing) controller.selectedAction = currentValue
                            Component.onCompleted: syncFromController()
                            Connections {
                                target: controller
                                function onTargetInfoChanged() { timerActionCombo.syncFromController() }
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 16

                NeonCard {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    cardColor: Theme.dialogPanel
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
                    cardColor: Theme.dialogPanel
                    cardBorderColor: Theme.e5BorderSoft
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 24
                        spacing: 18
                        Text { text: "指定时间"; color: Theme.textPrimary; font.pixelSize: 26; font.weight: Font.Bold }
                        Text { text: "设定今天的执行时刻；如果时间已过，会自动排到明天。"; color: Theme.textSecondary; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                        TimeInputPanel { id: fixedInput; Layout.fillWidth: true; Layout.preferredHeight: 126; showSeconds: false; hours: "23"; minutes: "00" }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10
                            Text { text: "重复规则"; color: Theme.textSecondary; font.pixelSize: 13 }
                            ComboBox {
                                id: repeatRuleCombo
                                Layout.preferredWidth: 150
                                Layout.preferredHeight: 34
                                model: [
                                    { label: "仅一次", value: "once" },
                                    { label: "每天", value: "daily" },
                                    { label: "工作日", value: "weekdays" },
                                    { label: "周末", value: "weekends" }
                                ]
                                textRole: "label"
                                valueRole: "value"
                                contentItem: Text {
                                    text: repeatRuleCombo.displayText
                                    color: Theme.textPrimary
                                    font.pixelSize: 13
                                    verticalAlignment: Text.AlignVCenter
                                    leftPadding: 10
                                    rightPadding: 26
                                    elide: Text.ElideRight
                                }
                                background: Rectangle {
                                    color: Theme.inputGlass
                                    radius: Theme.radiusSm
                                    border.color: Theme.e5BorderSoft
                                    border.width: 1
                                }
                            }
                        }
                        NeonButton {
                            Layout.preferredWidth: 180
                            Layout.preferredHeight: 44
                            variant: "primary"
                            text: "启动定时"
                            onClicked: controller.addFixedTimeTask("固定时间任务", mainWindow.safeInt(fixedInput.hours, 23), mainWindow.safeInt(fixedInput.minutes, 0), repeatRuleCombo.currentValue)
                        }
                        Text { text: "安全验证开启时只验证流程，不会真实执行系统动作。"; color: Theme.success; font.pixelSize: 13 }
                    }
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
                cardColor: Theme.dialogPanel
                cardBorderColor: Theme.e5BorderSoft
                ScrollView {
                    id: taskCenterScroll
                    anchors.fill: parent
                    clip: true
                    contentWidth: availableWidth
                    leftPadding: 20
                    rightPadding: 20
                    topPadding: 20
                    bottomPadding: 20
                    RowLayout {
                        id: taskCenterColumns
                        width: taskCenterScroll.availableWidth - taskCenterScroll.leftPadding - taskCenterScroll.rightPadding
                        spacing: 14

                        TaskTemplatePanel {
                            id: taskTemplateColumn
                            Layout.preferredWidth: 486
                            Layout.minimumWidth: 438
                            Layout.maximumWidth: 560
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            powerActionStepSummaryText: mainWindow.formatPowerActionStepSummary(controller.powerActionStepSummaryText)
                            onExecuteNowRequested: confirmDialog.open()
                        }

                        ColumnLayout {
                            id: queueAndActivityColumn
                            Layout.preferredWidth: 292
                            Layout.minimumWidth: 260
                            Layout.maximumWidth: 310
                            Layout.fillWidth: false
                            Layout.fillHeight: true
                            spacing: 10
                            TaskQueueDashboard {
                                Layout.fillWidth: true
                                Layout.rightMargin: 1
                                queueRows: mainWindow.queueRowModel
                            }
                            RecentActivityPanel {
                                Layout.rightMargin: 1
                                categorySummaryText: mainWindow.formatLogCategorySummary(controller.logCategorySummaryText)
                            }
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
                cardColor: Theme.dialogPanel
                cardBorderColor: Theme.e5BorderSoft
                ScrollView {
                    id: smartTriggerScroll
                    anchors.fill: parent
                    clip: true
                    contentWidth: availableWidth
                    leftPadding: 24
                    rightPadding: 24
                    topPadding: 24
                    bottomPadding: 24
                    ColumnLayout {
                        width: smartTriggerScroll.availableWidth
                        spacing: 14
                        Text { text: "智能触发"; color: Theme.textPrimary; font.pixelSize: 26; font.weight: Font.Bold }
                        Text {
                            Layout.fillWidth: true
                            property string diagnosticSource: controller.triggerHealthSummaryText
                            text: "当前触发摘要：进程=" + (controller.processTriggerActive ? "监控中" : "未启动")
                                  + " · 网络=" + (controller.networkTriggerActive ? "监控中" : "未启动")
                                  + " · 空闲=" + (controller.idleTriggerActive ? "检测中" : (controller.idleTriggerEnabled ? "已启用" : "未启动"))
                            color: Theme.textSecondary
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                        }
                        GridLayout {
                            id: smartTriggerTopGrid
                            Layout.fillWidth: true
                            columns: 2
                            rowSpacing: 14
                            columnSpacing: 14

                        NeonCard {
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            Layout.preferredHeight: 206
                            cardColor: Theme.dialogPanelRaised
                            cardBorderColor: Theme.borderStrong
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 16
                                spacing: 8
                                Text { text: "进程退出触发"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
                                Text { text: "监控指定进程；当进程出现后再退出，会按当前电源动作执行。安全验证会只记录模拟执行。"; color: Theme.textSecondary; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    Text { text: "进程名"; color: Theme.textSecondary; font.pixelSize: 13 }
                                    TextField {
                                        id: processNameInput
                                        Layout.fillWidth: true
                                        text: controller.processName
                                        color: Theme.textPrimary
                                        placeholderText: "notepad.exe"
                                        onTextChanged: controller.processName = text
                                        background: Rectangle { color: Theme.inputGlass; radius: Theme.radiusSm; border.color: Theme.e5BorderSoft; border.width: 1 }
                                    }
                                    Text { text: "轮询秒"; color: Theme.textSecondary; font.pixelSize: 13 }
                                    TextField {
                                        id: processPollInput
                                        Layout.preferredWidth: 70
                                        text: String(controller.processPollSeconds)
                                        horizontalAlignment: Text.AlignHCenter
                                        color: Theme.textPrimary
                                        validator: RegularExpressionValidator { regularExpression: /[0-9]*/ }
                                        onTextChanged: controller.processPollSeconds = mainWindow.safeInt(text, 5)
                                        background: Rectangle { color: Theme.inputGlass; radius: Theme.radiusSm; border.color: Theme.e5BorderSoft; border.width: 1 }
                                    }
                                }
                                Flow {
                                    id: processTriggerActions
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 64
                                    spacing: 10
                                    NeonButton { width: 142; height: 40; variant: "primary"; text: "开始监控"; enabled: !controller.processTriggerActive; onClicked: controller.startProcessTrigger() }
                                    NeonButton { width: 142; height: 40; variant: "secondary"; text: "停止监控"; enabled: controller.processTriggerActive; onClicked: controller.stopProcessTrigger() }
                                    Text { width: parent.width; text: controller.processTriggerStatus; color: controller.processTriggerActive ? Theme.warning : Theme.textSecondary; font.pixelSize: 13; elide: Text.ElideRight }
                                }
                            }
                        }
                        NeonCard {
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            Layout.preferredHeight: 242
                            cardColor: Theme.dialogPanelRaised
                            cardBorderColor: Theme.e5BorderBlue
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 16
                                spacing: 6
                                Text { text: "网络闲置触发"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
                                Text { text: "下载/上传速度持续低于阈值后执行当前电源动作。安全验证下只记录模拟执行。"; color: Theme.textSecondary; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                                GridLayout {
                                    id: networkThresholdGrid
                                    Layout.fillWidth: true
                                    columns: 4
                                    rowSpacing: 8
                                    columnSpacing: 8
                                    Text { text: "下载阈值"; color: Theme.textSecondary; font.pixelSize: 13 }
                                    TextField {
                                        Layout.preferredWidth: 76
                                        text: String(controller.networkDownloadThresholdKbps)
                                        horizontalAlignment: Text.AlignHCenter
                                        color: Theme.textPrimary
                                        onTextChanged: controller.networkDownloadThresholdKbps = mainWindow.safeFloat(text, 10.0)
                                        background: Rectangle { color: Theme.inputGlass; radius: Theme.radiusSm; border.color: Theme.e5BorderSoft; border.width: 1 }
                                    }
                                    Text { text: "上传阈值"; color: Theme.textSecondary; font.pixelSize: 13 }
                                    TextField {
                                        Layout.preferredWidth: 76
                                        text: String(controller.networkUploadThresholdKbps)
                                        horizontalAlignment: Text.AlignHCenter
                                        color: Theme.textPrimary
                                        onTextChanged: controller.networkUploadThresholdKbps = mainWindow.safeFloat(text, 10.0)
                                        background: Rectangle { color: Theme.inputGlass; radius: Theme.radiusSm; border.color: Theme.e5BorderSoft; border.width: 1 }
                                    }
                                    Text { text: "闲置秒数"; color: Theme.textSecondary; font.pixelSize: 13 }
                                    TextField {
                                        Layout.preferredWidth: 76
                                        text: String(controller.networkIdleSeconds)
                                        horizontalAlignment: Text.AlignHCenter
                                        color: Theme.textPrimary
                                        validator: RegularExpressionValidator { regularExpression: /[0-9]*/ }
                                        onTextChanged: controller.networkIdleSeconds = mainWindow.safeInt(text, 60)
                                        background: Rectangle { color: Theme.inputGlass; radius: Theme.radiusSm; border.color: Theme.e5BorderSoft; border.width: 1 }
                                    }
                                    Text { text: "轮询秒"; color: Theme.textSecondary; font.pixelSize: 13 }
                                    TextField {
                                        Layout.preferredWidth: 76
                                        text: String(controller.networkPollSeconds)
                                        horizontalAlignment: Text.AlignHCenter
                                        color: Theme.textPrimary
                                        validator: RegularExpressionValidator { regularExpression: /[0-9]*/ }
                                        onTextChanged: controller.networkPollSeconds = mainWindow.safeInt(text, 3)
                                        background: Rectangle { color: Theme.inputGlass; radius: Theme.radiusSm; border.color: Theme.e5BorderSoft; border.width: 1 }
                                    }
                                }
                                Flow {
                                    id: networkTriggerActions
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 62
                                    spacing: 10
                                    NeonButton { width: 142; height: 40; variant: "primary"; text: "开始网络监控"; enabled: !controller.networkTriggerActive; onClicked: controller.startNetworkTrigger() }
                                    NeonButton { width: 142; height: 40; variant: "secondary"; text: "停止网络监控"; enabled: controller.networkTriggerActive; onClicked: controller.stopNetworkTrigger() }
                                    Text { width: parent.width; text: controller.networkTriggerStatus; color: controller.networkTriggerActive ? Theme.warning : Theme.textSecondary; font.pixelSize: 13; elide: Text.ElideRight }
                                }
                                Text { text: controller.networkSpeedText; color: Theme.e5Blue; font.pixelSize: 13; font.weight: Font.Bold }
                            }
                        }
                        }
                        NeonCard {
                            id: idleTriggerPreviewSpacer
                            Layout.fillWidth: true
                            Layout.preferredHeight: 220
                            cardColor: Theme.dialogPanelRaised
                            cardBorderColor: Theme.e5BorderBlue
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 18
                                spacing: 8
                                Text { text: "空闲自动关机"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
                                Text { text: "检测键鼠无操作时间；达到阈值后把任务加入队列，继续复用安全验证、提醒、历史和取消逻辑。"; color: Theme.textSecondary; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                                RowLayout {
                                    id: idleTriggerControlRow
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 112
                                    spacing: 18

                                GridLayout {
                                    id: idleTriggerGrid
                                    Layout.preferredWidth: 236
                                    Layout.alignment: Qt.AlignTop
                                    columns: 2
                                    rowSpacing: 8
                                    columnSpacing: 8
                                    Text { text: "启用"; color: Theme.textSecondary; font.pixelSize: 13 }
                                    FluentSwitch { checked: controller.idleTriggerEnabled; onCheckedChanged: controller.idleTriggerEnabled = checked }
                                    Text { text: "空闲分钟"; color: Theme.textSecondary; font.pixelSize: 13 }
                                    TextField {
                                        Layout.preferredWidth: 76
                                        text: String(controller.idleMinutes)
                                        horizontalAlignment: Text.AlignHCenter
                                        color: Theme.textPrimary
                                        validator: RegularExpressionValidator { regularExpression: /[0-9]*/ }
                                        onTextChanged: controller.idleMinutes = mainWindow.safeInt(text, 30)
                                        background: Rectangle { color: Theme.inputGlass; radius: Theme.radiusSm; border.color: Theme.e5BorderSoft; border.width: 1 }
                                    }
                                    Text { text: "轮询秒"; color: Theme.textSecondary; font.pixelSize: 13 }
                                    TextField {
                                        Layout.preferredWidth: 76
                                        text: String(controller.idlePollSeconds)
                                        horizontalAlignment: Text.AlignHCenter
                                        color: Theme.textPrimary
                                        validator: RegularExpressionValidator { regularExpression: /[0-9]*/ }
                                        onTextChanged: controller.idlePollSeconds = mainWindow.safeInt(text, 10)
                                        background: Rectangle { color: Theme.inputGlass; radius: Theme.radiusSm; border.color: Theme.e5BorderSoft; border.width: 1 }
                                    }
                                }
                                Flow {
                                    id: idleTriggerActions
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 84
                                    Layout.alignment: Qt.AlignTop
                                    spacing: 10
                                    Text { width: 40; height: 40; verticalAlignment: Text.AlignVCenter; text: "动作"; color: Theme.textSecondary; font.pixelSize: 13 }
                                    ComboBox {
                                        id: idleActionCombo
                                        property bool syncing: true
                                        width: 128
                                        height: 40
                                        model: [
                                            { label: "关机", value: "shutdown" },
                                            { label: "睡眠", value: "sleep" },
                                            { label: "锁定", value: "lock" }
                                        ]
                                        textRole: "label"
                                        valueRole: "value"
                                        contentItem: Text {
                                            text: idleActionCombo.displayText
                                            color: Theme.textPrimary
                                            font.pixelSize: 13
                                            verticalAlignment: Text.AlignVCenter
                                            leftPadding: 10
                                            rightPadding: 26
                                            elide: Text.ElideRight
                                        }
                                        background: Rectangle {
                                            color: Theme.inputGlass
                                            radius: Theme.radiusSm
                                            border.color: Theme.e5BorderSoft
                                            border.width: 1
                                        }
                                        onCurrentValueChanged: if (!syncing) controller.idleAction = currentValue
                                        Component.onCompleted: {
                                            currentIndex = controller.idleAction === "sleep" ? 1 : (controller.idleAction === "lock" ? 2 : 0)
                                            syncing = false
                                        }
                                    }
                                    NeonButton { width: 142; height: 40; variant: "primary"; text: "开始空闲检测"; enabled: controller.idleTriggerEnabled && !controller.idleTriggerActive; onClicked: controller.startIdleTrigger() }
                                    NeonButton { width: 142; height: 40; variant: "secondary"; text: "停止空闲检测"; enabled: controller.idleTriggerActive; onClicked: controller.stopIdleTrigger() }
                                    Text { width: parent.width; text: controller.idleTriggerStatus; color: controller.idleTriggerActive ? Theme.warning : Theme.textSecondary; font.pixelSize: 13; elide: Text.ElideRight }
                                }
                                }
                            }
                        }
                        NeonCard {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 224
                            cardColor: Theme.dialogPanelRaised
                            cardBorderColor: Theme.e5BorderSoft
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 14
                                spacing: 6
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    Text { Layout.fillWidth: true; text: "触发日志"; color: Theme.textPrimary; font.pixelSize: 15; font.weight: Font.Bold }
                                }
                                GridLayout {
                                    id: supportActionGrid
                                    Layout.fillWidth: true
                                    columns: 3
                                    rowSpacing: 6
                                    columnSpacing: 6
                                    NeonButton { Layout.fillWidth: true; Layout.preferredHeight: 32; compact: true; variant: "secondary"; text: "清空日志"; onClicked: controller.clearLogs() }
                                    NeonButton { Layout.fillWidth: true; Layout.preferredHeight: 32; compact: true; variant: "primary"; text: "导出日志"; onClicked: controller.exportLogs() }
                                    NeonButton { Layout.fillWidth: true; Layout.preferredHeight: 32; compact: true; variant: "primary"; text: "导出诊断"; onClicked: controller.exportDiagnostics() }
                                    NeonButton { Layout.fillWidth: true; Layout.preferredHeight: 32; compact: true; variant: "secondary"; text: "复制诊断"; onClicked: controller.copyDiagnostics() }
                                    NeonButton { Layout.fillWidth: true; Layout.preferredHeight: 32; compact: true; variant: "secondary"; text: "健康检查"; onClicked: controller.runHealthCheck() }
                                }
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8
                                    NeonButton { Layout.preferredWidth: 64; Layout.preferredHeight: 30; compact: true; variant: controller.logFilter === "all" ? "primary" : "secondary"; text: "全部"; onClicked: controller.setLogFilter("all") }
                                    NeonButton { Layout.preferredWidth: 64; Layout.preferredHeight: 30; compact: true; variant: controller.logFilter === "warning" ? "primary" : "secondary"; text: "警告"; onClicked: controller.setLogFilter("warning") }
                                    NeonButton { Layout.preferredWidth: 64; Layout.preferredHeight: 30; compact: true; variant: controller.logFilter === "error" ? "primary" : "secondary"; text: "错误"; onClicked: controller.setLogFilter("error") }
                                    Text { Layout.fillWidth: true; text: controller.copyStatusText; color: Theme.textSecondary; font.pixelSize: 11; elide: Text.ElideRight; maximumLineCount: 1 }
                                }
                                Text { Layout.fillWidth: true; text: controller.healthCheckText; color: Theme.textSecondary; font.pixelSize: 11; wrapMode: Text.WordWrap; elide: Text.ElideRight; maximumLineCount: 3 }
                                Text { Layout.fillWidth: true; text: controller.diagnosticText; color: Theme.textSecondary; font.pixelSize: 11; wrapMode: Text.WordWrap; elide: Text.ElideRight; maximumLineCount: 5 }
                                Text { Layout.fillWidth: true; Layout.fillHeight: true; text: controller.filteredLogText; color: Theme.textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap; elide: Text.ElideRight }
                            }
                        }
                    }
                }
            }
        }

// Script page (4 脚本)
        Item {
            anchors.fill: parent
            visible: currentPage === 4

            NeonCard {
                anchors.fill: parent
                cardColor: Theme.dialogPanel
                cardBorderColor: Theme.e5BorderSoft
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 24
                    spacing: 14
                    Text { text: "执行前脚本"; color: Theme.textPrimary; font.pixelSize: 26; font.weight: Font.Bold }
                    Text {
                        Layout.fillWidth: true
                        text: "启用后，真实执行电源动作前会先运行脚本。安全验证下只记录将执行的脚本，不会启动外部程序。"
                        color: Theme.textSecondary
                        font.pixelSize: 14
                        wrapMode: Text.WordWrap
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Text { Layout.fillWidth: true; text: "启用执行前脚本"; color: Theme.textPrimary; font.pixelSize: 16; font.weight: Font.Bold }
                        FluentSwitch { checked: controller.scriptEnabled; onCheckedChanged: controller.scriptEnabled = checked }
                    }
                    Text { text: "脚本路径"; color: Theme.textPrimary; font.pixelSize: 16; font.weight: Font.Bold }
                    TextField {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 44
                        text: controller.scriptPath
                        placeholderText: "C:/scripts/before-shutdown.bat"
                        color: Theme.textPrimary
                        onTextChanged: controller.scriptPath = text
                        background: Rectangle { color: Theme.inputGlass; radius: Theme.radiusSm; border.color: Theme.e5BorderSoft; border.width: 1 }
                    }
                    Flow {
                        id: scriptActionFlow
                        Layout.fillWidth: true
                        Layout.preferredHeight: 86
                        spacing: 10
                        Text { text: "超时秒数"; color: Theme.textSecondary; font.pixelSize: 13 }
                        TextField {
                            width: 92
                            height: 40
                            text: String(controller.scriptTimeoutSeconds)
                            horizontalAlignment: Text.AlignHCenter
                            color: Theme.textPrimary
                            validator: RegularExpressionValidator { regularExpression: /[0-9]*/ }
                            onTextChanged: controller.scriptTimeoutSeconds = mainWindow.safeInt(text, 10)
                            background: Rectangle { color: Theme.inputGlass; radius: Theme.radiusSm; border.color: Theme.e5BorderSoft; border.width: 1 }
                        }
                        NeonButton { width: 138; height: 40; variant: "primary"; text: "测试脚本"; onClicked: controller.testScript() }
                        NeonButton { width: 112; height: 40; variant: "secondary"; text: "验证路径"; onClicked: controller.validateScriptPath() }
                        NeonButton { width: 112; height: 40; variant: "secondary"; text: "打开目录"; onClicked: controller.openScriptFolder() }
                    }
                    NeonCard {
                        id: scriptLogPanel
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        cardColor: Theme.dialogPanelRaised
                        cardBorderColor: Theme.e5BorderSoft
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 14
                            spacing: 8
                            RowLayout {
                                id: scriptLogStatusStrip
                                Layout.fillWidth: true
                                spacing: 12
                                Text { Layout.fillWidth: true; text: "脚本与执行日志"; color: Theme.textPrimary; font.pixelSize: 15; font.weight: Font.Bold; elide: Text.ElideRight }
                                Text { text: controller.scriptEnabled ? "已启用" : "未启用"; color: controller.scriptEnabled ? Theme.success : Theme.textSecondary; font.pixelSize: 12; font.weight: Font.Bold }
                                Text { text: "超时 " + controller.scriptTimeoutSeconds + " 秒"; color: Theme.textSecondary; font.pixelSize: 12 }
                                Text { text: controller.scriptPath ? "路径已填写" : "路径未填写"; color: controller.scriptPath ? Theme.success : Theme.warning; font.pixelSize: 12; font.weight: Font.Bold }
                            }
                            Rectangle {
                                id: scriptLogViewport
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                radius: Theme.radiusMd
                                color: Theme.glassSoft
                                border.color: Theme.e5BorderSoft
                                border.width: 1
                                clip: true

                                Text {
                                    anchors.fill: parent
                                    anchors.margins: 12
                                    text: controller.logText
                                    color: Theme.textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                    elide: Text.ElideRight
                                }
                            }
                        }
                    }
                }
            }
        }

        // Settings page (5 设置)
        Item {
            anchors.fill: parent
            visible: currentPage === 5

            NeonCard {
                anchors.fill: parent
                cardColor: Theme.dialogPanel
                cardBorderColor: Theme.e5BorderSoft
                ScrollView {
                    id: settingsScroll
                    anchors.fill: parent
                    clip: true
                    contentWidth: availableWidth
                    leftPadding: 24
                    rightPadding: 24
                    topPadding: 24
                    bottomPadding: 24

                    ColumnLayout {
                        width: settingsScroll.availableWidth
                        spacing: 14
                        Text { text: "设置"; color: Theme.textPrimary; font.pixelSize: 26; font.weight: Font.Bold }
                        Text {
                            Layout.fillWidth: true
                            property string diagnosticSource: controller.safetySummaryText
                            text: "当前安全摘要：" + (controller.dryRun ? "安全验证中" : "真实执行模式")
                                  + " · 动作：" + controller.actionLabel
                                  + " · 脚本：" + (controller.scriptEnabled ? "开启" : "关闭")
                                  + " · 优雅关闭应用：" + (controller.closeAppsBeforeAction ? "开启" : "关闭")
                            color: Theme.textSecondary
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                        }

                        GridLayout {
                            id: settingsPanelGrid
                            Layout.fillWidth: true
                            Layout.preferredHeight: 490
                            columns: 2
                            rowSpacing: 14
                            columnSpacing: 14

                            NeonCard {
                                id: settingsSafetyPanel
                                Layout.fillWidth: true
                                Layout.preferredWidth: (settingsPanelGrid.width - settingsPanelGrid.columnSpacing) / 2
                                Layout.preferredHeight: 286
                                Layout.row: 0
                                Layout.column: 0
                                cardColor: Theme.dialogPanelRaised
                                cardBorderColor: Theme.borderStrong
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 16
                                    spacing: 10
                                    Text { text: "安全执行"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 16
                                        Text { Layout.preferredWidth: 190; text: "安全验证模式"; color: Theme.textPrimary; font.pixelSize: 15; font.weight: Font.Bold }
                                        FluentSwitch {
                                            id: dryRunSafetySwitch
                                            enabled: !controller.powerActionInProgress
                                            checked: controller.dryRun
                                            onCheckedChanged: mainWindow.confirmLiveModeFromSwitch(checked)
                                        }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 16
                                        Text { Layout.preferredWidth: 190; text: "强制关闭应用"; color: Theme.textPrimary; font.pixelSize: 15; font.weight: Font.Bold }
                                        FluentSwitch {
                                            enabled: !controller.powerActionInProgress
                                            checked: controller.forceClose
                                            onCheckedChanged: controller.forceClose = checked
                                        }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 16
                                        Text { Layout.preferredWidth: 190; text: "关机前优雅关闭应用"; color: Theme.textPrimary; font.pixelSize: 15; font.weight: Font.Bold }
                                        FluentSwitch {
                                            enabled: !controller.powerActionInProgress
                                            checked: controller.closeAppsBeforeAction
                                            onCheckedChanged: controller.closeAppsBeforeAction = checked
                                        }
                                    }
                                    GridLayout {
                                        Layout.fillWidth: true
                                        columns: 2
                                        rowSpacing: 8
                                        columnSpacing: 12
                                        Text { text: "等待超时"; color: Theme.textSecondary; font.pixelSize: 13 }
                                        TextField {
                                            Layout.preferredWidth: 112
                                            enabled: controller.closeAppsBeforeAction && !controller.powerActionInProgress
                                            text: String(controller.closeAppsTimeoutSeconds)
                                            inputMethodHints: Qt.ImhDigitsOnly
                                            validator: IntValidator { bottom: 1; top: 300 }
                                            onEditingFinished: controller.closeAppsTimeoutSeconds = mainWindow.safeInt(text, 20)
                                            background: Rectangle { color: Theme.inputGlass; radius: Theme.radiusSm; border.color: Theme.e5BorderSoft; border.width: 1 }
                                        }
                                        Text { text: "预检"; color: Theme.textSecondary; font.pixelSize: 13 }
                                        NeonButton {
                                            Layout.preferredWidth: 138
                                            Layout.preferredHeight: 34
                                            compact: true
                                            variant: "secondary"
                                            text: "预检关闭应用"
                                            enabled: !controller.powerActionInProgress
                                            onClicked: controller.previewCloseApps()
                                        }
                                    }
                                    Text { Layout.fillWidth: true; text: "1-300 秒；预检只列出将请求关闭的窗口，不会真正关闭应用。"; color: Theme.textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap; maximumLineCount: 2 }
                                    Text { Layout.fillWidth: true; text: "预检：" + controller.closeAppsPreviewText + " · 最近结果：" + controller.closeAppsLastResultText; color: Theme.textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap; maximumLineCount: 2 }
                                }
                            }

                            NeonCard {
                                id: settingsReminderPanel
                                Layout.fillWidth: true
                                Layout.preferredWidth: (settingsPanelGrid.width - settingsPanelGrid.columnSpacing) / 2
                                Layout.preferredHeight: 206
                                Layout.row: 0
                                Layout.column: 1
                                cardColor: Theme.dialogPanelRaised
                                cardBorderColor: Theme.e5BorderBlue
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 16
                                    spacing: 10
                                    Text { text: "提醒与通知"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 16
                                        Text { Layout.preferredWidth: 190; text: "启动时自动播放音乐"; color: Theme.textPrimary; font.pixelSize: 15; font.weight: Font.Bold }
                                        FluentSwitch { checked: controller.musicAutoplayEnabled; onCheckedChanged: controller.musicAutoplayEnabled = checked }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 16
                                        Text { Layout.preferredWidth: 190; text: "执行前提醒"; color: Theme.textPrimary; font.pixelSize: 15; font.weight: Font.Bold }
                                        FluentSwitch { checked: controller.reminderEnabled; onCheckedChanged: controller.reminderEnabled = checked }
                                    }
                                    GridLayout {
                                        Layout.fillWidth: true
                                        columns: 2
                                        rowSpacing: 8
                                        columnSpacing: 12
                                        Text { text: "提醒分钟"; color: Theme.textSecondary; font.pixelSize: 13 }
                                        TextField {
                                            Layout.preferredWidth: 210
                                            text: controller.reminderMinutesCsv
                                            placeholderText: "10,5,1"
                                            onEditingFinished: controller.reminderMinutesCsv = text
                                            background: Rectangle { color: Theme.inputGlass; radius: Theme.radiusSm; border.color: Theme.e5BorderSoft; border.width: 1 }
                                        }
                                        Text { text: "默认延后"; color: Theme.textSecondary; font.pixelSize: 13 }
                                        TextField {
                                            Layout.preferredWidth: 112
                                            text: String(controller.snoozeMinutesValue)
                                            inputMethodHints: Qt.ImhDigitsOnly
                                            onEditingFinished: controller.snoozeMinutesValue = mainWindow.safeInt(text, 15)
                                            background: Rectangle { color: Theme.inputGlass; radius: Theme.radiusSm; border.color: Theme.e5BorderSoft; border.width: 1 }
                                        }
                                    }
                                    Text { Layout.fillWidth: true; text: "提醒分钟用逗号分隔，例如 10,5,1；默认延后用于提醒弹窗。"; color: Theme.textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap; maximumLineCount: 2 }
                                }
                            }

                            NeonCard {
                                id: settingsSystemPanel
                                Layout.fillWidth: true
                                Layout.preferredWidth: (settingsPanelGrid.width - settingsPanelGrid.columnSpacing) / 2
                                Layout.preferredHeight: 190
                                Layout.row: 1
                                Layout.column: 1
                                cardColor: Theme.dialogPanelRaised
                                cardBorderColor: Theme.e5BorderSoft
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 16
                                    spacing: 8
                                    Text { text: "系统与历史"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 16
                                        Text { Layout.preferredWidth: 190; text: "Windows 原生通知"; color: Theme.textPrimary; font.pixelSize: 15; font.weight: Font.Bold }
                                        FluentSwitch { checked: controller.windowsNotificationsEnabled; onCheckedChanged: controller.windowsNotificationsEnabled = checked }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 16
                                        Text { Layout.preferredWidth: 190; text: "开机自动启动"; color: Theme.textPrimary; font.pixelSize: 15; font.weight: Font.Bold }
                                        FluentSwitch { checked: controller.startWithWindows; onCheckedChanged: controller.startWithWindows = checked }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 12
                                        Text { Layout.preferredWidth: 76; text: "任务历史"; color: Theme.textSecondary; font.pixelSize: 13 }
                                        TextField {
                                            Layout.preferredWidth: 82
                                            text: String(controller.taskHistoryLimit)
                                            inputMethodHints: Qt.ImhDigitsOnly
                                            onEditingFinished: controller.taskHistoryLimit = mainWindow.safeInt(text, 500)
                                            background: Rectangle { color: Theme.inputGlass; radius: Theme.radiusSm; border.color: Theme.e5BorderSoft; border.width: 1 }
                                        }
                                        Flow {
                                            id: historyActionFlow
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 34
                                            spacing: 8
                                            NeonButton { width: 78; height: 34; compact: true; variant: "secondary"; text: "清空历史"; onClicked: controller.clearHistory() }
                                            NeonButton { width: 78; height: 34; compact: true; variant: "primary"; text: "导出历史"; onClicked: controller.exportHistory() }
                                        }
                                    }
                                    Text { Layout.fillWidth: true; text: mainWindow.historyRowModel.length > 0 ? ("最近历史：" + mainWindow.historyRowModel[0].message) : "任务历史：暂无记录"; color: Theme.textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap; maximumLineCount: 2 }
                                }
                            }

                            NeonCard {
                                id: settingsLiveModeWarning
                                Layout.fillWidth: true
                                Layout.preferredWidth: (settingsPanelGrid.width - settingsPanelGrid.columnSpacing) / 2
                                Layout.preferredHeight: 190
                                Layout.row: 1
                                Layout.column: 0
                                cardColor: Theme.dialogPanelRaised
                                cardBorderColor: Theme.danger
                                hoverable: false

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 16
                                    spacing: 8

                                    Text { text: "真实执行提醒"; color: Theme.danger; font.pixelSize: 18; font.weight: Font.Bold }
                                    Text {
                                        Layout.fillWidth: true
                                        text: "真实执行模式会执行真实系统动作。建议验证时保持安全验证开启；立即执行按钮会再次弹窗确认，倒计时和进程/网络触发到点后不会再次确认。"
                                        color: Theme.textSecondary
                                        font.pixelSize: 12
                                        wrapMode: Text.WordWrap
                                        maximumLineCount: 3
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        text: "托盘可用时关闭窗口会隐藏到后台；托盘不可用时关闭窗口不会继续后台运行。请使用托盘菜单“退出程序”显式退出。"
                                        color: Theme.textSecondary
                                        font.pixelSize: 12
                                        wrapMode: Text.WordWrap
                                        maximumLineCount: 2
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Window {
        id: musicPlayerWindow
        objectName: "musicPlayerWindow"
        width: 560
        height: 560
        minimumWidth: 480
        minimumHeight: 520
        visible: false
        title: "音乐播放器"
        color: Theme.bgDeep

        FolderDialog {
            id: musicFolderDialog
            title: "选择音乐文件夹"
        }

        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                GradientStop { position: 0.0; color: Theme.e5BgA }
                GradientStop { position: 1.0; color: Theme.e5BgC }
            }
        }

        NeonCard {
            anchors.fill: parent
            anchors.margins: 18
            cardColor: Theme.dialogPanelRaised
            cardBorderColor: Theme.borderStrong
            radius: Theme.radiusXl

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 22
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        Layout.fillWidth: true
                        text: "音乐播放器"
                        color: Theme.textPrimary
                        font.pixelSize: 24
                        font.weight: Font.Bold
                    }
                    NeonButton {
                        Layout.preferredWidth: 138
                        Layout.preferredHeight: 36
                        compact: true
                        text: "选择音乐文件夹"
                        onClicked: controller.chooseMusicFolder()
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: controller.musicAvailable ? controller.musicTitle : "未找到音乐文件"
                    color: controller.musicAvailable ? Theme.textPrimary : Theme.danger
                    font.pixelSize: 15
                    wrapMode: Text.WordWrap
                }

                Text {
                    Layout.fillWidth: true
                    text: "文件夹：" + controller.musicFolder
                    color: Theme.textSecondary
                    font.pixelSize: 12
                    elide: Text.ElideMiddle
                }

                Text {
                    Layout.fillWidth: true
                    text: "歌曲列表"
                    color: Theme.textPrimary
                    font.pixelSize: 14
                    font.weight: Font.Bold
                }

                Rectangle {
                    id: musicPlaylistFrame
                    Layout.fillWidth: true
                    Layout.preferredHeight: 130
                    radius: Theme.radiusMd
                    color: Theme.glassSoft
                    border.color: Theme.e5BorderSoft
                    border.width: 1
                    clip: true

                    ListView {
                        anchors.fill: parent
                        anchors.margins: 8
                        clip: true
                        model: mainWindow.musicTrackModel
                        delegate: Rectangle {
                            width: ListView.view.width
                            height: 34
                            radius: 8
                            color: controller.musicCurrentIndex === index ? Theme.cardGlassActive : "transparent"
                            border.color: controller.musicCurrentIndex === index ? Theme.borderStrong : "transparent"
                            Text {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
                                verticalAlignment: Text.AlignVCenter
                                text: modelData.title
                                color: controller.musicCurrentIndex === index ? Theme.textPrimary : Theme.textSecondary
                                font.pixelSize: 13
                                elide: Text.ElideRight
                            }
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: controller.playMusicTrack(index)
                            }
                        }
                    }

                    Item {
                        id: musicEmptyPlaylistState
                        anchors.fill: parent
                        visible: mainWindow.musicTrackModel.length === 0

                        Column {
                            anchors.centerIn: parent
                            spacing: 4
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: "暂无歌曲"
                                color: Theme.textPrimary
                                font.pixelSize: 15
                                font.weight: Font.Bold
                            }
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: "选择包含 MP3 的文件夹"
                                color: Theme.textSecondary
                                font.pixelSize: 12
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    NeonButton {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 42
                        variant: "ghost"
                        text: "上一首"
                        onClicked: controller.previousMusicTrack()
                    }
                    NeonButton {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 42
                        variant: "primary"
                        text: controller.musicPlaying ? "暂停" : "播放"
                        onClicked: controller.musicPlaying ? controller.pauseMusic() : controller.playMusic()
                    }
                    NeonButton {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 42
                        variant: "ghost"
                        text: "下一首"
                        onClicked: controller.nextMusicTrack()
                    }
                    NeonButton {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 42
                        variant: "ghost"
                        text: "停止"
                        onClicked: controller.stopMusic()
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    NeonButton {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 34
                        compact: true
                        variant: controller.musicPlaybackMode === "sequence" ? "primary" : "ghost"
                        text: "顺序播放"
                        onClicked: controller.setMusicPlaybackMode("sequence")
                    }
                    NeonButton {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 34
                        compact: true
                        variant: controller.musicPlaybackMode === "list_loop" ? "primary" : "ghost"
                        text: "列表循环"
                        onClicked: controller.setMusicPlaybackMode("list_loop")
                    }
                    NeonButton {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 34
                        compact: true
                        variant: controller.musicPlaybackMode === "single_loop" ? "primary" : "ghost"
                        text: "单曲循环"
                        onClicked: controller.setMusicPlaybackMode("single_loop")
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: "播放进度：" + controller.musicPositionText + " / " + controller.musicDurationText
                    color: Theme.textSecondary
                    font.pixelSize: 13
                }

                Slider {
                    Layout.fillWidth: true
                    from: 0
                    to: Math.max(1, controller.musicDurationMs)
                    stepSize: 1000
                    value: controller.musicPositionMs
                    onMoved: controller.seekMusic(value)
                }

                Text {
                    Layout.fillWidth: true
                    text: "音量：" + controller.musicVolume + "%"
                    color: Theme.textSecondary
                    font.pixelSize: 13
                }

                Slider {
                    Layout.fillWidth: true
                    from: 0
                    to: 100
                    stepSize: 1
                    value: controller.musicVolume
                    onMoved: controller.setMusicVolume(value)
                }
            }
        }
    }

    Dialog {
        id: firstRunSafetyGuideDialog
        modal: true
        standardButtons: Dialog.NoButton
        width: 500
        padding: 22
        anchors.centerIn: parent

        Overlay.modal: Rectangle {
            color: Theme.dialogScrim
        }

        background: Rectangle {
            color: Theme.dialogPanel
            radius: Theme.radiusLg
            border.color: Theme.warning
            border.width: 1
            antialiasing: true
        }

        contentItem: ColumnLayout {
            spacing: Theme.spaceMd
            Text { Layout.fillWidth: true; text: "首次启动安全说明"; color: Theme.textPrimary; font.pixelSize: 20; font.weight: Font.Bold }
            Text { Layout.fillWidth: true; text: "安全验证模式默认开启：应用只记录将要执行的动作，不会真实关机、重启、睡眠、休眠、注销、锁定或运行脚本。"; color: Theme.textSecondary; font.pixelSize: 14; wrapMode: Text.WordWrap }
            Text { Layout.fillWidth: true; text: "关闭安全验证后可能真实执行 Windows 电源动作，请先确认任务、触发器、脚本路径和未保存工作。"; color: Theme.danger; font.pixelSize: 14; wrapMode: Text.WordWrap }
            Text { Layout.fillWidth: true; text: "右下角托盘可用时，关闭窗口会隐藏到后台，倒计时、队列和触发器仍会继续。"; color: Theme.textSecondary; font.pixelSize: 14; wrapMode: Text.WordWrap }
            Text { Layout.fillWidth: true; text: "如需彻底退出，请右键右下角托盘图标并选择“退出程序”。"; color: Theme.textSecondary; font.pixelSize: 14; wrapMode: Text.WordWrap }
        }

        footer: Item {
            implicitHeight: 64
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 22
                anchors.rightMargin: 22
                anchors.bottomMargin: 16
                Item { Layout.fillWidth: true }
                NeonButton {
                    compact: true
                    variant: "primary"
                    text: "我知道了"
                    onClicked: {
                        controller.acknowledgeFirstRunSafetyGuide()
                        firstRunSafetyGuideDialog.close()
                    }
                }
            }
        }
    }

    Dialog {
        id: trayCloseHintDialog
        modal: true
        standardButtons: Dialog.NoButton
        width: 480
        padding: 22
        anchors.centerIn: parent

        Overlay.modal: Rectangle {
            color: Theme.dialogScrim
        }

        background: Rectangle {
            color: Theme.dialogPanel
            radius: Theme.radiusLg
            border.color: Theme.primary
            border.width: 1
            antialiasing: true
        }

        contentItem: ColumnLayout {
            spacing: Theme.spaceMd
            Text { Layout.fillWidth: true; text: "将隐藏到右下角托盘"; color: Theme.textPrimary; font.pixelSize: 20; font.weight: Font.Bold }
            Text { Layout.fillWidth: true; text: "任务、倒计时和触发器仍会继续运行。"; color: Theme.textSecondary; font.pixelSize: 14; wrapMode: Text.WordWrap }
            Text { Layout.fillWidth: true; text: "要彻底退出，请右键右下角托盘图标选择“退出程序”。"; color: Theme.textSecondary; font.pixelSize: 14; wrapMode: Text.WordWrap }
        }

        footer: Item {
            implicitHeight: 64
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 22
                anchors.rightMargin: 22
                anchors.bottomMargin: 16
                Item { Layout.fillWidth: true }
                NeonButton {
                    compact: true
                    variant: "primary"
                    text: "隐藏到托盘"
                    onClicked: {
                        controller.acknowledgeTrayCloseHint()
                        trayCloseHintDialog.close()
                        controller.minimizeToTray()
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

    Dialog {
        id: reminderDialog
        modal: true
        title: controller.reminderDialogTitle
        standardButtons: Dialog.NoButton
        anchors.centerIn: parent
        width: 440

        Overlay.modal: Rectangle {
            color: Theme.dialogScrim
        }

        background: Rectangle {
            radius: Theme.radiusLg
            color: Theme.dialogPanel
            border.color: controller.dryRun ? Theme.success : Theme.danger
            border.width: 1
            antialiasing: true
        }

        contentItem: ColumnLayout {
            spacing: 14
            Text {
                Layout.fillWidth: true
                text: controller.reminderDialogBody
                color: Theme.textPrimary
                font.pixelSize: 14
                wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                NeonButton {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 38
                    compact: true
                    text: controller.reminderDialogSnoozeText
                    onClicked: {
                        controller.snoozeCurrentTask()
                        reminderDialog.close()
                    }
                }
                NeonButton {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 38
                    compact: true
                    variant: "danger"
                    text: "取消当前任务"
                    onClicked: {
                        controller.cancelCurrentTask()
                        reminderDialog.close()
                    }
                }
                NeonButton {
                    Layout.preferredWidth: 92
                    Layout.preferredHeight: 38
                    compact: true
                    variant: "secondary"
                    text: "知道了"
                    onClicked: reminderDialog.close()
                }
            }
        }
    }

    Dialog {
        id: liveModeConfirmDialog
        modal: true
        standardButtons: Dialog.NoButton
        width: 460
        height: 286
        padding: 22
        anchors.centerIn: parent

        Overlay.modal: Rectangle {
            color: Theme.dialogScrim
        }

        background: Rectangle {
            color: Theme.dialogPanel
            radius: Theme.radiusLg
            border.color: Theme.danger
            border.width: 1
            antialiasing: true
        }

        contentItem: ColumnLayout {
            spacing: Theme.spaceMd
            Text {
                Layout.fillWidth: true
                text: "确认关闭安全验证"
                color: Theme.textPrimary
                font.pixelSize: 20
                font.weight: Font.Bold
            }
            Text {
                Layout.fillWidth: true
                text: "关闭安全验证后将进入真实执行模式，倒计时结束、进程退出触发、网络闲置触发和立即执行都可能执行真实系统电源动作。\n\n请确认动作、触发器、脚本路径和未保存工作。"
                color: Theme.textSecondary
                font.pixelSize: 14
                lineHeight: 1.16
                wrapMode: Text.WordWrap
            }
            Item { Layout.fillHeight: true }
        }

        footer: Item {
            implicitHeight: 64
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 22
                anchors.rightMargin: 22
                anchors.bottomMargin: 16
                spacing: Theme.spaceSm
                Item { Layout.fillWidth: true }
                NeonButton {
                    compact: true
                    text: "取消"
                    onClicked: liveModeConfirmDialog.reject()
                }
                NeonButton {
                    compact: true
                    variant: "danger"
                    text: "进入真实执行模式"
                    onClicked: liveModeConfirmDialog.accept()
                }
            }
        }

        onAccepted: controller.requestDryRunChange(false)
        onRejected: mainWindow.syncDryRunSwitchState()
        onClosed: mainWindow.syncDryRunSwitchState()
    }
}
