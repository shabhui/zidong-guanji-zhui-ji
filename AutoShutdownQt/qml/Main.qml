import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Window {
    id: mainWindow
    width: 1180
    height: 760
    minimumWidth: 1040
    minimumHeight: 680
    visible: true
    title: "定时关机助手 v5.0"
    color: Theme.workspaceBackground
    flags: Qt.Window | Qt.FramelessWindowHint

    property int currentPage: 0
    property bool trayCloseRequested: false
    property var queueRowModel: parseRows(controller.queueRowsJson)
    property var historyRowModel: parseRows(controller.historyRowsJson)
    property var musicTrackModel: parseRows(controller.musicTracksJson)
    property var workspaceNavItems: [
        { label: "总览", detail: "状态与快速启动", icon: "●" },
        { label: "定时", detail: "倒计时与指定时间", icon: "T" },
        { label: "任务", detail: "队列与执行记录", icon: "≡" },
        { label: "智能触发", detail: "进程、网络与空闲", icon: "S" },
        { label: "脚本", detail: "自动化与诊断", icon: "{}" },
        { label: "设置", detail: "安全与偏好", icon: "⚙" }
    ]

    function parseRows(jsonText) {
        try { return JSON.parse(jsonText) } catch (error) { return [] }
    }

    function selectWorkspacePage(index) {
        if (index >= 0 && index < workspaceNavItems.length) currentPage = index
    }

    function statusLabel() {
        if (controller.status === "running") return "运行中"
        if (controller.status === "paused") return "已暂停"
        return "就绪"
    }

    function toggleMaximized() {
        visibility === Window.Maximized ? showNormal() : showMaximized()
    }

    function syncDryRunSwitchState() {
        workspaceV5.syncDryRunSwitchState()
    }

    function confirmLiveModeFromSwitch(checked) {
        if (checked === controller.dryRun) return
        if (checked) {
            controller.requestDryRunChange(true)
        } else {
            syncDryRunSwitchState()
            liveModeConfirmDialog.open()
        }
    }

    function openMusicPlayer() {
        musicPlayerWindow.show()
        musicPlayerWindow.raise()
        musicPlayerWindow.requestActivate()
    }

    function requestImmediateExecution() {
        immediateConfirmDialog.open()
    }

    Connections {
        target: controller
        function onTaskQueueChanged() { mainWindow.queueRowModel = mainWindow.parseRows(controller.queueRowsJson) }
        function onHistoryChanged() { mainWindow.historyRowModel = mainWindow.parseRows(controller.historyRowsJson) }
        function onMusicChanged() { mainWindow.musicTrackModel = mainWindow.parseRows(controller.musicTracksJson) }
        function onDryRunChanged() { mainWindow.syncDryRunSwitchState() }
        function onReminderChanged() { if (controller.reminderDialogTitle !== "") reminderDialog.open() }
    }

    Component.onCompleted: {
        if (!controller.firstRunSafetyGuideShown) firstRunSafetyGuideDialog.open()
    }

    onClosing: function(close) {
        if (controller.trayAvailable && !trayCloseRequested) {
            close.accepted = false
            if (!controller.trayCloseHintShown) trayCloseHintDialog.open()
            else controller.minimizeToTray()
        }
    }

    WorkspaceV5 {
        id: workspaceV5
        anchors.fill: parent
        rootWindow: mainWindow
    }

    Window {
        id: musicPlayerWindow
        objectName: "musicPlayerWindow"
        width: 650
        height: 500
        minimumWidth: 560
        minimumHeight: 420
        visible: false
        title: "音乐播放器"
        color: Theme.workspaceBackground

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12

            V5Section {
                Layout.fillWidth: true
                Layout.preferredHeight: 98
                title: controller.musicAvailable ? controller.musicTitle : "未找到音乐"
                subtitle: controller.musicFolder
                accentColor: Theme.animeAtmosphereSakura
                RowLayout {
                    Layout.fillWidth: true
                    NeonButton { compact: true; text: "选择文件夹"; onClicked: controller.chooseMusicFolder() }
                    NeonButton { compact: true; text: "上一首"; onClicked: controller.previousMusicTrack() }
                    NeonButton { compact: true; variant: "primary"; text: controller.musicPlaying ? "暂停" : "播放"; onClicked: controller.musicPlaying ? controller.pauseMusic() : controller.playMusic() }
                    NeonButton { compact: true; text: "下一首"; onClicked: controller.nextMusicTrack() }
                    NeonButton { compact: true; text: "停止"; onClicked: controller.stopMusic() }
                    Item { Layout.fillWidth: true }
                    V5StatusPill { text: controller.musicPositionText + " / " + controller.musicDurationText; accentColor: Theme.workspaceCyan }
                }
            }

            V5Section {
                Layout.fillWidth: true
                Layout.fillHeight: true
                title: "播放列表"
                subtitle: "共 " + String(mainWindow.musicTrackModel.length) + " 首"
                ListView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    model: mainWindow.musicTrackModel
                    spacing: 6
                    clip: true
                    delegate: Rectangle {
                        required property var modelData
                        required property int index
                        width: ListView.view.width
                        height: 44
                        radius: Theme.controlRadius
                        color: controller.musicCurrentIndex === index ? Theme.controlSurfaceSelected : Theme.controlSurface
                        border.color: controller.musicCurrentIndex === index ? Theme.workspaceAccent : Theme.controlBorder
                        border.width: 1
                        Text { anchors.left: parent.left; anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; anchors.margins: 12; text: modelData.title || modelData.name || String(modelData); color: Theme.workspaceInk; font.pixelSize: 12; elide: Text.ElideRight }
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: controller.playMusicTrack(index) }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Text { text: "音量 " + controller.musicVolume + "%"; color: Theme.workspaceMuted; font.pixelSize: 11 }
                Slider { Layout.fillWidth: true; from: 0; to: 100; value: controller.musicVolume; onMoved: controller.setMusicVolume(value) }
                NeonButton { compact: true; variant: controller.musicPlaybackMode === "sequence" ? "primary" : "secondary"; text: "顺序"; onClicked: controller.setMusicPlaybackMode("sequence") }
                NeonButton { compact: true; variant: controller.musicPlaybackMode === "list_loop" ? "primary" : "secondary"; text: "列表循环"; onClicked: controller.setMusicPlaybackMode("list_loop") }
                NeonButton { compact: true; variant: controller.musicPlaybackMode === "single_loop" ? "primary" : "secondary"; text: "单曲循环"; onClicked: controller.setMusicPlaybackMode("single_loop") }
            }
        }
    }

    Dialog {
        id: firstRunSafetyGuideDialog
        modal: true
        standardButtons: Dialog.NoButton
        anchors.centerIn: parent
        width: 500
        height: 330
        padding: 22
        Overlay.modal: Rectangle { color: Theme.dialogScrim }
        background: Rectangle { radius: Theme.panelRadius; color: Theme.dialogPanel; border.color: Theme.workspaceAccent; border.width: 1 }
        contentItem: ColumnLayout {
            spacing: 12
            Text { Layout.fillWidth: true; text: "欢迎使用 v5.0"; color: Theme.workspaceInk; font.pixelSize: 22; font.weight: Font.Bold }
            Text { Layout.fillWidth: true; text: "默认开启安全验证：所有倒计时、触发器、脚本和立即执行都只验证流程，不会执行真实系统电源动作。\n\n确认配置无误后，可在设置页切换到真实执行模式。"; color: Theme.workspaceMuted; font.pixelSize: 13; wrapMode: Text.WordWrap; lineHeight: 1.2 }
            Item { Layout.fillHeight: true }
            NeonButton { Layout.fillWidth: true; variant: "primary"; text: "开始使用"; onClicked: { controller.acknowledgeFirstRunSafetyGuide(); firstRunSafetyGuideDialog.accept() } }
        }
    }

    Dialog {
        id: trayCloseHintDialog
        modal: true
        standardButtons: Dialog.NoButton
        anchors.centerIn: parent
        width: 430
        height: 220
        padding: 22
        Overlay.modal: Rectangle { color: Theme.dialogScrim }
        background: Rectangle { radius: Theme.panelRadius; color: Theme.dialogPanel; border.color: Theme.controlBorder; border.width: 1 }
        contentItem: ColumnLayout {
            Text { Layout.fillWidth: true; text: "应用将继续在托盘运行"; color: Theme.workspaceInk; font.pixelSize: 18; font.weight: Font.Bold }
            Text { Layout.fillWidth: true; text: "关闭窗口不会停止任务。需要彻底退出时，请在设置页点击“退出应用”。"; color: Theme.workspaceMuted; font.pixelSize: 12; wrapMode: Text.WordWrap }
            Item { Layout.fillHeight: true }
            NeonButton { Layout.fillWidth: true; variant: "primary"; text: "知道了，最小化到托盘"; onClicked: { controller.acknowledgeTrayCloseHint(); trayCloseHintDialog.accept(); controller.minimizeToTray() } }
        }
    }

    ConfirmDialog {
        id: immediateConfirmDialog
        anchors.centerIn: parent
        actionLabel: controller.actionLabel
    }

    Dialog {
        id: reminderDialog
        modal: true
        standardButtons: Dialog.NoButton
        anchors.centerIn: parent
        width: 450
        height: 250
        padding: 22
        title: controller.reminderDialogTitle
        Overlay.modal: Rectangle { color: Theme.dialogScrim }
        background: Rectangle { radius: Theme.panelRadius; color: Theme.dialogPanel; border.color: controller.dryRun ? Theme.workspaceSuccess : Theme.workspaceDanger; border.width: 1 }
        contentItem: ColumnLayout {
            Text { Layout.fillWidth: true; text: controller.reminderDialogBody; color: Theme.workspaceInk; font.pixelSize: 13; wrapMode: Text.WordWrap }
            Item { Layout.fillHeight: true }
            RowLayout {
                Layout.fillWidth: true
                NeonButton { Layout.fillWidth: true; text: controller.reminderDialogSnoozeText; onClicked: { controller.snoozeCurrentTask(); reminderDialog.close() } }
                NeonButton { Layout.fillWidth: true; variant: "quietDanger"; text: "取消任务"; onClicked: { controller.cancelCurrentTask(); reminderDialog.close() } }
                NeonButton { text: "知道了"; onClicked: reminderDialog.close() }
            }
        }
    }

    Dialog {
        id: liveModeConfirmDialog
        modal: true
        standardButtons: Dialog.NoButton
        anchors.centerIn: parent
        width: 490
        height: 290
        padding: 22
        Overlay.modal: Rectangle { color: Theme.dialogScrim }
        background: Rectangle { radius: Theme.panelRadius; color: Theme.dialogPanel; border.color: Theme.workspaceDanger; border.width: 1 }
        contentItem: ColumnLayout {
            Text { Layout.fillWidth: true; text: "确认进入真实执行模式"; color: Theme.workspaceInk; font.pixelSize: 20; font.weight: Font.Bold }
            Text { Layout.fillWidth: true; text: "关闭安全验证后，倒计时结束、智能触发和立即执行可能真实关机、重启、睡眠、休眠、注销或锁定。请先保存工作并检查脚本。"; color: Theme.workspaceDanger; font.pixelSize: 13; wrapMode: Text.WordWrap; lineHeight: 1.2 }
            Item { Layout.fillHeight: true }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                NeonButton { text: "取消"; onClicked: liveModeConfirmDialog.reject() }
                NeonButton { variant: "danger"; text: "确认真实执行"; onClicked: liveModeConfirmDialog.accept() }
            }
        }
        onAccepted: controller.requestDryRunChange(false)
        onRejected: mainWindow.syncDryRunSwitchState()
        onClosed: mainWindow.syncDryRunSwitchState()
    }
}
