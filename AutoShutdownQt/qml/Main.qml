import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import QtMultimedia
import "components"

Window {
    id: mainWindow
    width: 1120
    height: 720
    minimumWidth: 1040
    minimumHeight: 680
    visible: true
    title: "定时关机助手 v4.0"
    color: Theme.bgDeep
    flags: Qt.Window | Qt.FramelessWindowHint

    property int currentPage: 0
    property bool dryRunSwitchSyncing: false
    property bool trayCloseRequested: false
    property var queueRowModel: queueRows()
    property var musicTrackModel: musicTracks()
    property var historyRowModel: historyRows()
    property string feibiAction: "idle"
    property bool feibiPaused: false
    property bool feibiManualMode: false
    property bool feibiVoiceActive: false
    property int feibiAmbientStep: 0
    property int feibiInteractionStep: 0
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

    function setFeibiAction(actionName, autoReturnMs, manualMode) {
        feibiAction = actionName
        feibiReturnTimer.stop()
        if (manualMode === true) {
            mainWindow.feibiManualMode = true
        } else if (autoReturnMs > 0) {
            mainWindow.feibiManualMode = false
        }
        if (autoReturnMs > 0) {
            feibiReturnTimer.interval = autoReturnMs
            feibiReturnTimer.restart()
        }
    }

    function playFeibiVoice(sourceUrl) {
        mainWindow.feibiPaused = false
        mainWindow.feibiManualMode = false
        feibiVoicePlayer.stop()
        feibiVoicePlayer.source = Qt.resolvedUrl(sourceUrl)
        feibiVoicePlayer.play()
        setFeibiAction("talk", 5200, false)
    }

    function toggleFeibiPaused() {
        mainWindow.feibiPaused = !mainWindow.feibiPaused
        if (mainWindow.feibiPaused) {
            feibiVoicePlayer.pause()
        }
    }

    function interactWithFeibi() {
        mainWindow.feibiPaused = false
        mainWindow.feibiManualMode = true
        mainWindow.feibiInteractionStep = (mainWindow.feibiInteractionStep + 1) % 4
        var actions = ["push", "eating", "sleep", "talk"]
        var actionName = actions[mainWindow.feibiInteractionStep]
        mainWindow.setFeibiAction(actionName, 0, true)
        if (actionName === "talk") {
            feibiVoicePlayer.stop()
            feibiVoicePlayer.source = Qt.resolvedUrl("assets/feibi/sounds/feibi-chuubi.mp3")
            feibiVoicePlayer.play()
        }
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

    AudioOutput { id: feibiVoiceOutput; volume: 0.58 }

    MediaPlayer {
        id: feibiVoicePlayer
        audioOutput: feibiVoiceOutput
        onPlaybackStateChanged: {
            mainWindow.feibiVoiceActive = playbackState === MediaPlayer.PlayingState
            if (playbackState === MediaPlayer.StoppedState && mainWindow.feibiAction === "talk" && !mainWindow.feibiManualMode && !feibiReturnTimer.running) {
                mainWindow.setFeibiAction("idle", 0)
            }
        }
    }

    Timer {
        id: feibiReturnTimer
        repeat: false
        onTriggered: mainWindow.setFeibiAction("idle", 0)
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

    Image {
        id: xingStyleBackground
        anchors.fill: parent
        source: "assets/blog-dashboard-bg.png"
        fillMode: Image.PreserveAspectCrop
        smooth: true
        mipmap: true
    }

    Rectangle {
        anchors.fill: parent
        color: "#62061124"
    }

    // Editorial depth layers behind the work surface.
    Rectangle {
        id: panelWashTop
        x: outerMargin
        y: topBarHeight
        width: parent.width - outerMargin * 2
        height: 260
        radius: Theme.radiusXl
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#2A67D8EF" }
            GradientStop { position: 0.52; color: "#24FF7A9B" }
            GradientStop { position: 1.0; color: "#147DFFC4" }
        }
        opacity: 0.42
    }

    Rectangle {
        id: panelWashBottom
        x: outerMargin
        y: parent.height - 210
        width: parent.width - outerMargin * 2
        height: 170
        radius: Theme.radiusXl
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#1AFFB86B" }
            GradientStop { position: 0.55; color: "#217C5CFF" }
            GradientStop { position: 1.0; color: "#0067D8EF" }
        }
        opacity: 0.34
    }

    NeonCard {
        id: appShell
        x: outerMargin - 8
        y: topBarHeight + 6
        width: parent.width - outerMargin * 2 + 16
        height: parent.height - topBarHeight - outerMargin - 4
        radius: 30
        cardColor: Theme.blogShell
        cardBorderColor: "#28FFFFFF"
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
        color: Theme.blogNavPanel
        border.color: "#2FFFFFFF"
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
            spacing: 12

            Rectangle {
                Layout.preferredWidth: 40
                Layout.preferredHeight: 40
                radius: 15
                gradient: Gradient {
                    GradientStop { position: 0.0; color: Theme.blogAvatarRingA }
                    GradientStop { position: 1.0; color: Theme.blogAvatarRingB }
                }
                Image {
                    anchors.fill: parent
                    anchors.margins: 4
                    source: "../app_icon.png"
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true
                }
            }

            ColumnLayout {
                Layout.preferredWidth: 250
                spacing: 0
                Text {
                    text: "定时关机助手"
                    color: Theme.textPrimary
                    font.pixelSize: 20
                    font.weight: Font.Bold
                    elide: Text.ElideRight
                }
                Text {
                    text: "v4.0 · 电源控制台"
                    color: Theme.commandCool
                    font.pixelSize: 12
                    elide: Text.ElideRight
                }
            }

            Item { Layout.fillWidth: true }

            Rectangle {
                Layout.preferredWidth: statusText.implicitWidth + 26
                Layout.preferredHeight: 32
                radius: 16
                color: "#3AFFFFFF"
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
                Layout.preferredWidth: dryRunText.implicitWidth + 26
                Layout.preferredHeight: 32
                radius: 16
                color: controller.dryRun ? "#3362F6B5" : "#33FF5C8A"
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
                Layout.preferredWidth: 92
                Layout.preferredHeight: 34
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
                Layout.preferredHeight: 34
                compact: true
                variant: "ghost"
                text: "-"
                ToolTip.visible: hovered
                ToolTip.delay: 400
                ToolTip.text: "最小化"
                onClicked: mainWindow.showMinimized()
            }
            NeonButton {
                Layout.preferredWidth: 38
                Layout.preferredHeight: 34
                compact: true
                variant: "ghost"
                text: mainWindow.visibility === Window.Maximized ? "□" : "▣"
                ToolTip.visible: hovered
                ToolTip.delay: 400
                ToolTip.text: "最大化/还原"
                onClicked: mainWindow.toggleMaximized()
            }
            NeonButton {
                Layout.preferredWidth: 38
                Layout.preferredHeight: 34
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
        x: outerMargin + 300
        y: topBarHeight + 10
        width: parent.width - outerMargin * 2 - 600
        height: 44
        z: 3
        cardColor: Theme.blogGlassPanel
        cardBorderColor: Theme.blogCardBorder
        radius: 22

        RowLayout {
            id: blogTopNavigation
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 12
            spacing: 4

            Repeater {
                model: pageNames
                delegate: Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 30
                    radius: 15
                    color: currentPage === index ? "#446366F1" : (navMouse.containsMouse ? "#22FFFFFF" : "transparent")
                    border.color: currentPage === index ? "#80FFFFFF" : "transparent"
                    border.width: 1
                    Text {
                        anchors.centerIn: parent
                        text: modelData
                        color: currentPage === index ? Theme.textPrimary : Theme.textSecondary
                        font.pixelSize: 12
                        font.weight: currentPage === index ? Font.Bold : Font.DemiBold
                    }
                    MouseArea {
                        id: navMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: currentPage = index
                    }
                }
            }
        }
    }

    Item {
        id: contentHost
        x: outerMargin
        y: topBarHeight + outerMargin + 48
        width: parent.width - outerMargin * 2
        height: parent.height - y - outerMargin
        z: 1

        // Overview page
        Item {
            id: blogHomeDashboard
            anchors.fill: parent
            visible: currentPage === 0

            Item {
                id: animeMotionOverlay
                anchors.fill: parent
                clip: true

                Image {
                    id: animeSkylineLayer
                    x: -32
                    y: -18
                    width: parent.width + 64
                    height: parent.height + 44
                    source: "assets/anime-skyline-bg.png"
                    fillMode: Image.PreserveAspectCrop
                    smooth: true
                    mipmap: true
                    opacity: 0.42

                    SequentialAnimation on x {
                        id: backgroundDriftAnimation
                        loops: Animation.Infinite
                        NumberAnimation { from: -32; to: 0; duration: 14500; easing.type: Easing.InOutSine }
                        NumberAnimation { from: 0; to: -32; duration: 14500; easing.type: Easing.InOutSine }
                    }
                }

                Item {
                    id: animeStarfield
                    anchors.fill: parent
                    Repeater {
                        model: 34
                        Rectangle {
                            x: ((index * 79) % 100) / 100 * animeStarfield.width
                            y: ((index * 47) % 82) / 100 * animeStarfield.height
                            width: 2 + (index % 3)
                            height: width
                            radius: width / 2
                            color: index % 4 === 0 ? Theme.animeSakura : Theme.animeCyanGlow
                            opacity: 0.22 + (index % 5) * 0.045
                            SequentialAnimation on opacity {
                                loops: Animation.Infinite
                                NumberAnimation { to: 0.82; duration: 1100 + index * 35; easing.type: Easing.InOutSine }
                                NumberAnimation { to: 0.18; duration: 1300 + index * 28; easing.type: Easing.InOutSine }
                            }
                        }
                    }
                }

                Rectangle {
                    id: shootingStarLayer
                    x: -180
                    y: 62
                    width: 155
                    height: 3
                    radius: 2
                    rotation: -15
                    opacity: 0.0
                    gradient: Gradient {
                        orientation: Gradient.Horizontal
                        GradientStop { position: 0.0; color: "#00FFFFFF" }
                        GradientStop { position: 0.72; color: Theme.animeCyanGlow }
                        GradientStop { position: 1.0; color: Theme.animeSakura }
                    }
                    SequentialAnimation {
                        id: shootingStarTravelAnimation
                        running: blogHomeDashboard.visible
                        loops: Animation.Infinite
                        PauseAnimation { duration: 1900 }
                        ParallelAnimation {
                            NumberAnimation { target: shootingStarLayer; property: "x"; from: -180; to: animeMotionOverlay.width + 80; duration: 1850; easing.type: Easing.OutCubic }
                            NumberAnimation { target: shootingStarLayer; property: "y"; from: 62; to: 16; duration: 1850; easing.type: Easing.OutCubic }
                            SequentialAnimation {
                                NumberAnimation { target: shootingStarLayer; property: "opacity"; from: 0.0; to: 0.92; duration: 260 }
                                NumberAnimation { target: shootingStarLayer; property: "opacity"; to: 0.0; duration: 820 }
                            }
                        }
                    }
                }

                Item {
                    id: petalParticleLayer
                    anchors.fill: parent
                    y: -18
                    Repeater {
                        model: 18
                        Rectangle {
                            x: ((index * 61) % 100) / 100 * petalParticleLayer.width
                            y: ((index * 37) % 100) / 100 * petalParticleLayer.height
                            width: 7 + (index % 4)
                            height: 4 + (index % 3)
                            radius: height / 2
                            rotation: index * 23
                            color: Theme.animeSakura
                            opacity: 0.22 + (index % 4) * 0.05
                            SequentialAnimation on rotation {
                                loops: Animation.Infinite
                                NumberAnimation { from: index * 23; to: index * 23 + 360; duration: 5200 + index * 130 }
                            }
                        }
                    }
                    SequentialAnimation on y {
                        id: petalFallAnimation
                        loops: Animation.Infinite
                        NumberAnimation { from: -18; to: 28; duration: 7200; easing.type: Easing.InOutSine }
                        NumberAnimation { from: 28; to: -18; duration: 7200; easing.type: Easing.InOutSine }
                    }
                }
            }

            Item {
                id: overviewWorkbench
                anchors.fill: parent
                readonly property int overviewGap: 16
                readonly property int heroRowHeight: 190
                readonly property int lyricBarHeight: 70
                readonly property int contentRowY: heroRowHeight + overviewGap + lyricBarHeight + overviewGap
                readonly property int contentRowHeight: height - contentRowY
                readonly property int profileWidth: Math.round((width - overviewGap) * 0.58)
                readonly property int musicWidth: width - profileWidth - overviewGap
                readonly property int contentLeftWidth: 330
                readonly property int contentRightWidth: width - contentLeftWidth - overviewGap

                NeonCard {
                    id: blogProfileCard
                    x: 0
                    y: 0
                    width: overviewWorkbench.profileWidth
                    height: overviewWorkbench.heroRowHeight
                    radius: 28
                    cardColor: Theme.blogGlassPanel
                    cardBorderColor: Theme.blogCardBorder

                    SequentialAnimation on y {
                        id: profileFloatAnimation
                        loops: Animation.Infinite
                        NumberAnimation { from: 0; to: -5; duration: 2600; easing.type: Easing.InOutSine }
                        NumberAnimation { from: -5; to: 0; duration: 2600; easing.type: Easing.InOutSine }
                    }

                    RowLayout {
                        z: 1
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 24
                        spacing: 20

                        Rectangle {
                            id: profileAvatarFrame
                            Layout.preferredWidth: 86
                            Layout.preferredHeight: 86
                            radius: 22
                            gradient: Gradient {
                                GradientStop { position: 0.0; color: Theme.blogAvatarRingA }
                                GradientStop { position: 1.0; color: Theme.blogAvatarRingB }
                            }
                            Image {
                                anchors.fill: parent
                                anchors.margins: 5
                                source: "../app_icon.png"
                                fillMode: Image.PreserveAspectFit
                                smooth: true
                                mipmap: true
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Text { text: "AutoShutdownQt"; color: Theme.textPrimary; font.pixelSize: 32; font.weight: Font.Bold; elide: Text.ElideRight }
                            Text {
                                Layout.fillWidth: true
                                text: "像博客首页一样，把倒计时、安全验证、队列和系统动作收进一张夜空玻璃仪表盘。"
                                color: Theme.textSecondary
                                font.pixelSize: 14
                                wrapMode: Text.WordWrap
                                maximumLineCount: 2
                            }
                        }
                    }

                    GridLayout {
                        id: profileStatsRow
                        anchors.left: parent.left
                        anchors.bottom: parent.bottom
                        anchors.leftMargin: 28
                        anchors.bottomMargin: 20
                        width: 260
                        columns: 3
                        columnSpacing: 18
                        rowSpacing: 0
                        ColumnLayout { spacing: 0; Text { text: String(mainWindow.queueRowModel.length); color: Theme.commandCool; font.pixelSize: 24; font.weight: Font.Black } Text { text: "队列"; color: Theme.textSecondary; font.pixelSize: 11 } }
                        ColumnLayout { spacing: 0; Text { text: controller.status === "running" ? "ON" : "OK"; color: Theme.commandRose; font.pixelSize: 24; font.weight: Font.Black } Text { text: "状态"; color: Theme.textSecondary; font.pixelSize: 11 } }
                        ColumnLayout { spacing: 0; Text { text: controller.dryRun ? "安全" : "真实"; color: Theme.commandEmerald; font.pixelSize: 24; font.weight: Font.Black } Text { text: "模式"; color: Theme.textSecondary; font.pixelSize: 11 } }
                    }

                    RowLayout {
                        z: 2
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        anchors.rightMargin: 24
                        anchors.bottomMargin: 22
                        spacing: 10
                        NeonButton { Layout.preferredWidth: 104; Layout.preferredHeight: 36; compact: true; variant: "primary"; text: "启动 30 分钟"; onClicked: controller.startCountdown(0, 30, 0) }
                        NeonButton { Layout.preferredWidth: 92; Layout.preferredHeight: 36; compact: true; variant: "secondary"; text: "取消"; enabled: controller.status === "running"; onClicked: controller.cancel() }
                    }
                }

                NeonCard {
                    id: quickCountdownPanel
                    x: overviewWorkbench.profileWidth + overviewWorkbench.overviewGap
                    y: 0
                    width: overviewWorkbench.musicWidth
                    height: overviewWorkbench.heroRowHeight
                    radius: 28
                    cardColor: Theme.blogGlassPanel
                    cardBorderColor: Theme.blogCardBorder

                    Rectangle {
                        id: mascotHaloPulse
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.rightMargin: 16
                        anchors.topMargin: 18
                        width: 118
                        height: 118
                        radius: 59
                        color: "#229B7CFF"
                        border.color: Theme.animeSakura
                        border.width: 1
                        opacity: 0.48
                        z: 0
                        SequentialAnimation on scale {
                            loops: Animation.Infinite
                            NumberAnimation { from: 0.94; to: 1.08; duration: 1800; easing.type: Easing.InOutSine }
                            NumberAnimation { from: 1.08; to: 0.94; duration: 1800; easing.type: Easing.InOutSine }
                        }
                    }

                    Image {
                        id: mascotCharacterSprite
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.rightMargin: 12
                        anchors.topMargin: 10
                        width: 96
                        height: 142
                        source: "assets/anime-mascot.png"
                        fillMode: Image.PreserveAspectFit
                        smooth: true
                        mipmap: true
                        opacity: 0.20
                        z: 0.5
                        SequentialAnimation on y {
                            id: mascotFloatAnimation
                            loops: Animation.Infinite
                            NumberAnimation { from: 0; to: -6; duration: 2200; easing.type: Easing.InOutSine }
                            NumberAnimation { from: -6; to: 0; duration: 2200; easing.type: Easing.InOutSine }
                        }
                    }

                    Item {
                        id: feibiPetStage
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.rightMargin: 8
                        anchors.topMargin: 8
                        width: 172
                        height: 170
                        z: 2

                        Rectangle {
                            id: feibiStageHalo
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.top: parent.top
                            anchors.topMargin: 22
                            width: 128
                            height: 128
                            radius: 64
                            color: "#1828D7FF"
                            border.color: mainWindow.feibiVoiceActive ? Theme.animeSakura : Theme.animeCyanGlow
                            border.width: 1
                            opacity: mainWindow.feibiVoiceActive ? 1.0 : 0.76
                            SequentialAnimation on scale {
                                id: feibiStagePulseAnimation
                                loops: Animation.Infinite
                                NumberAnimation { from: 0.94; to: 1.07; duration: 1600; easing.type: Easing.InOutSine }
                                NumberAnimation { from: 1.07; to: 0.94; duration: 1600; easing.type: Easing.InOutSine }
                            }
                        }

                        Rectangle {
                            id: feibiSpeechBubble
                            anchors.left: parent.left
                            anchors.top: parent.top
                            anchors.leftMargin: 4
                            anchors.topMargin: 0
                            width: 92
                            height: 30
                            radius: 15
                            color: "#D01A243A"
                            border.color: mainWindow.feibiVoiceActive ? Theme.animeSakura : Theme.animeCyanGlow
                            border.width: 1
                            opacity: mainWindow.feibiVoiceActive || feibiStageMouse.containsMouse ? 0.96 : 0.72
                            Text {
                                anchors.centerIn: parent
                                text: mainWindow.feibiAction === "talk" ? "菲比播报中"
                                      : mainWindow.feibiAction === "sleep" ? "休眠巡逻"
                                      : mainWindow.feibiAction === "eating" ? "补充能量"
                                      : mainWindow.feibiAction === "push" ? "别偷懒"
                                      : "菲比待命"
                                color: Theme.textPrimary
                                font.pixelSize: 10
                                font.weight: Font.Bold
                                maximumLineCount: 1
                            }
                        }

                        Rectangle {
                            id: feibiStateBadge
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.rightMargin: 16
                            anchors.topMargin: 12
                            width: 18
                            height: 18
                            radius: 9
                            color: mainWindow.feibiVoiceActive ? Theme.animeSakura : Theme.commandEmerald
                            border.color: "#CCFFFFFF"
                            SequentialAnimation on opacity {
                                loops: Animation.Infinite
                                NumberAnimation { from: 0.55; to: 1.0; duration: 700; easing.type: Easing.InOutSine }
                                NumberAnimation { from: 1.0; to: 0.55; duration: 700; easing.type: Easing.InOutSine }
                            }
                        }

                        Rectangle {
                            id: feibiGroundShadow
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.bottom: feibiControlDock.top
                            anchors.bottomMargin: 2
                            width: 86
                            height: 18
                            radius: 9
                            color: "#66000000"
                            opacity: 0.46
                            SequentialAnimation on width {
                                loops: Animation.Infinite
                                NumberAnimation { from: 76; to: 98; duration: 1800; easing.type: Easing.InOutSine }
                                NumberAnimation { from: 98; to: 76; duration: 1800; easing.type: Easing.InOutSine }
                            }
                        }

                        AnimatedImage {
                            id: feibiDesktopPetSprite
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.bottom: feibiControlDock.top
                            anchors.bottomMargin: -4
                            width: 150
                            height: 134
                            source: mainWindow.feibiAction === "talk" ? "assets/feibi/gifs/talk.gif"
                                    : mainWindow.feibiAction === "push" ? "assets/feibi/gifs/push.gif"
                                    : mainWindow.feibiAction === "sleep" ? "assets/feibi/gifs/sleep.gif"
                                    : mainWindow.feibiAction === "eating" ? "assets/feibi/gifs/eating.gif"
                                    : "assets/feibi/gifs/idle.gif"
                            fillMode: Image.PreserveAspectFit
                            playing: blogHomeDashboard.visible && !mainWindow.feibiPaused
                            smooth: false
                            opacity: 0.98
                            transform: [
                                Translate { id: feibiSpriteFloatTransform; y: 0 },
                                Rotation {
                                    id: feibiSpriteTiltTransform
                                    origin.x: feibiDesktopPetSprite.width / 2
                                    origin.y: feibiDesktopPetSprite.height
                                    angle: 0
                                }
                            ]
                            SequentialAnimation {
                                id: feibiDockFloatAnimation
                                running: blogHomeDashboard.visible && !mainWindow.feibiPaused
                                loops: Animation.Infinite
                                NumberAnimation { target: feibiSpriteFloatTransform; property: "y"; from: 0; to: -7; duration: 1900; easing.type: Easing.InOutSine }
                                NumberAnimation { target: feibiSpriteFloatTransform; property: "y"; from: -7; to: 0; duration: 1900; easing.type: Easing.InOutSine }
                            }
                            SequentialAnimation {
                                running: blogHomeDashboard.visible && !mainWindow.feibiPaused
                                loops: Animation.Infinite
                                NumberAnimation { target: feibiSpriteTiltTransform; property: "angle"; from: -1.0; to: 1.0; duration: 2400; easing.type: Easing.InOutSine }
                                NumberAnimation { target: feibiSpriteTiltTransform; property: "angle"; from: 1.0; to: -1.0; duration: 2400; easing.type: Easing.InOutSine }
                            }
                        }

                        Item {
                            id: feibiControlDock
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.bottom: parent.bottom
                            width: 132
                            height: 28
                            z: 5

                            Row {
                                anchors.fill: parent
                                spacing: 6

                                Rectangle {
                                    id: feibiPlayButton
                                    width: 40
                                    height: 26
                                    radius: 13
                                    color: "#3328D7FF"
                                    border.color: Theme.animeCyanGlow
                                    Text { anchors.centerIn: parent; text: "播放"; color: Theme.textPrimary; font.pixelSize: 10; font.weight: Font.Bold }
                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: mainWindow.playFeibiVoice("assets/feibi/sounds/feibi-call.mp3")
                                    }
                                }
                                Rectangle {
                                    id: feibiPauseButton
                                    width: 40
                                    height: 26
                                    radius: 13
                                    color: mainWindow.feibiPaused ? "#4462F6B5" : "#3346F1A8"
                                    border.color: mainWindow.feibiPaused ? Theme.commandEmerald : Theme.borderStrong
                                    Text { anchors.centerIn: parent; text: mainWindow.feibiPaused ? "继续" : "暂停"; color: Theme.textPrimary; font.pixelSize: 10; font.weight: Font.Bold }
                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: mainWindow.toggleFeibiPaused()
                                    }
                                }
                                Rectangle {
                                    id: feibiInteractButton
                                    width: 40
                                    height: 26
                                    radius: 13
                                    color: "#33FF8ACF"
                                    border.color: Theme.animeSakura
                                    Text { anchors.centerIn: parent; text: "互动"; color: Theme.textPrimary; font.pixelSize: 10; font.weight: Font.Bold }
                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: mainWindow.interactWithFeibi()
                                    }
                                }
                            }
                        }

                        MouseArea {
                            id: feibiStageMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: mainWindow.playFeibiVoice("assets/feibi/sounds/feibi-call.mp3")
                            onEntered: mainWindow.setFeibiAction("push", 1600)
                        }

                        Row {
                            id: feibiVoiceEqualizer
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.bottom: feibiControlDock.top
                            anchors.bottomMargin: 2
                            spacing: 4
                            opacity: mainWindow.feibiVoiceActive ? 0.95 : 0.0
                            Repeater {
                                model: 5
                                Rectangle {
                                    width: 4
                                    height: 8 + index * 2
                                    radius: 2
                                    color: index % 2 === 0 ? Theme.animeCyanGlow : Theme.animeSakura
                                    SequentialAnimation on height {
                                        running: blogHomeDashboard.visible && mainWindow.feibiVoiceActive
                                        loops: Animation.Infinite
                                        NumberAnimation { to: 22 - index * 2; duration: 260 + index * 40; easing.type: Easing.InOutSine }
                                        NumberAnimation { to: 8 + index * 2; duration: 300 + index * 35; easing.type: Easing.InOutSine }
                                    }
                                }
                            }
                        }
                    }

                    Timer {
                        id: feibiAmbientActionTimer
                        running: blogHomeDashboard.visible && !mainWindow.feibiPaused
                        repeat: true
                        interval: 6800
                        onTriggered: {
                            if (mainWindow.feibiPaused || mainWindow.feibiManualMode || mainWindow.feibiVoiceActive) return
                            mainWindow.feibiAmbientStep = (mainWindow.feibiAmbientStep + 1) % 4
                            if (mainWindow.feibiAmbientStep === 1) {
                                mainWindow.setFeibiAction("push", 4200, false)
                            } else if (mainWindow.feibiAmbientStep === 2) {
                                mainWindow.setFeibiAction("eating", 5200, false)
                            } else if (mainWindow.feibiAmbientStep === 3) {
                                mainWindow.setFeibiAction("sleep", 6200, false)
                            } else {
                                mainWindow.setFeibiAction("idle", 0, false)
                            }
                        }
                    }

                    ColumnLayout {
                        id: commandShortcutRail
                        anchors.fill: parent
                        anchors.margins: 24
                        anchors.rightMargin: 194
                        spacing: 12
                        z: 1

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 14
                            Rectangle {
                                Layout.preferredWidth: 68
                                Layout.preferredHeight: 68
                                radius: 34
                                color: "#26343D6D"
                                border.color: "#80FFFFFF"
                                Text { anchors.centerIn: parent; text: "♪"; color: "white"; font.pixelSize: 28; font.weight: Font.Bold }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                Text { id: cloudMusicBadge; text: "CLOUD TIMER"; color: Theme.commandCool; font.pixelSize: 11; font.weight: Font.Black }
                                Text { text: "快捷倒计时"; color: Theme.textPrimary; font.pixelSize: 24; font.weight: Font.Bold; elide: Text.ElideRight }
                                Text { text: "Preset Deck"; color: Theme.textSecondary; font.pixelSize: 12 }
                            }
                        }

                        GridLayout {
                            id: quickChipRow
                            Layout.fillWidth: true
                            columns: 2
                            rowSpacing: 8
                            columnSpacing: 10
                            NeonButton {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 38
                                compact: true
                                text: "15 分钟"
                                onClicked: {
                                    controller.startCountdown(0, 15, 0)
                                    mainWindow.playFeibiVoice("assets/feibi/sounds/time.mp3")
                                }
                            }
                            NeonButton {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 38
                                compact: true
                                text: "30 分钟"
                                onClicked: {
                                    controller.startCountdown(0, 30, 0)
                                    mainWindow.playFeibiVoice("assets/feibi/sounds/time.mp3")
                                }
                            }
                            NeonButton {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 38
                                compact: true
                                text: "1 小时"
                                onClicked: {
                                    controller.startCountdown(1, 0, 0)
                                    mainWindow.playFeibiVoice("assets/feibi/sounds/time.mp3")
                                }
                            }
                            NeonButton {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 38
                                compact: true
                                text: "2 小时"
                                onClicked: {
                                    controller.startCountdown(2, 0, 0)
                                    mainWindow.playFeibiVoice("assets/feibi/sounds/time.mp3")
                                }
                            }
                        }
                    }
                }

                NeonCard {
                    id: lyricCommandBar
                    x: 0
                    y: overviewWorkbench.heroRowHeight + overviewWorkbench.overviewGap
                    width: parent.width
                    height: overviewWorkbench.lyricBarHeight
                    radius: 24
                    cardColor: Theme.blogLyricPanel
                    cardBorderColor: Theme.blogCardBorder

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 28
                        anchors.rightMargin: 28
                        spacing: 18

                        Row {
                            id: lyricWaveBars
                            Layout.preferredWidth: 70
                            Layout.preferredHeight: 34
                            spacing: 5
                            anchors.verticalCenter: parent.verticalCenter
                            Repeater {
                                model: [10, 14, 18, 22, 16]
                                Rectangle {
                                    width: 6
                                    height: modelData
                                    radius: 3
                                    color: index % 2 === 0 ? Theme.animeCyanGlow : Theme.animeSakura
                                    opacity: controller.status === "running" ? 0.95 : 0.42
                                    anchors.bottom: parent.bottom
                                    transformOrigin: Item.Bottom
                                    SequentialAnimation on scale {
                                        id: lyricWavePulseAnimation
                                        loops: Animation.Infinite
                                        NumberAnimation { from: 0.72; to: 1.35; duration: 540 + index * 80; easing.type: Easing.InOutSine }
                                        NumberAnimation { from: 1.35; to: 0.72; duration: 540 + index * 80; easing.type: Easing.InOutSine }
                                    }
                                }
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Text {
                                Layout.fillWidth: true
                                text: mainWindow.queueRowModel.length > 0 ? "下一任务：" + mainWindow.queueRowModel[0].name : "后台托盘 · 安全验证已开启 · 暂无排队任务"
                                color: Theme.textPrimary
                                font.pixelSize: 18
                                font.weight: Font.Bold
                                horizontalAlignment: Text.AlignHCenter
                                elide: Text.ElideRight
                            }
                            Text {
                                Layout.fillWidth: true
                                text: controller.powerActionProgressText
                                color: Theme.textSecondary
                                font.pixelSize: 11
                                horizontalAlignment: Text.AlignHCenter
                                elide: Text.ElideRight
                            }
                        }

                        Rectangle {
                            id: siteDashboardStrip
                            Layout.preferredWidth: 86
                            Layout.preferredHeight: 34
                            radius: 17
                            color: "#24343D6D"
                            border.color: "#33FFFFFF"
                            Text { anchors.centerIn: parent; text: controller.status === "running" ? "ON" : "OK"; color: Theme.commandEmerald; font.pixelSize: 12; font.weight: Font.Black }
                        }
                    }
                }

                NeonCard {
                    id: currentTaskPanel
                    x: 0
                    y: overviewWorkbench.contentRowY
                    width: overviewWorkbench.contentLeftWidth
                    height: overviewWorkbench.contentRowHeight
                    radius: 28
                    cardColor: Theme.blogGlassPanel
                    cardBorderColor: Theme.blogCardBorder
                    clip: true

                    Image { anchors.fill: parent; source: "assets/blog-post-cover.png"; fillMode: Image.PreserveAspectCrop; smooth: true; mipmap: true; opacity: 0.34 }
                    Image { id: animeTaskCoverLayer; anchors.fill: parent; source: "assets/anime-task-cover.png"; fillMode: Image.PreserveAspectCrop; smooth: true; mipmap: true; opacity: 0.88 }
                    Rectangle { anchors.fill: parent; color: Theme.blogImageScrim }

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 5
                        Item { Layout.fillHeight: true }
                        Text { text: "LATEST TASK"; color: "white"; font.pixelSize: 11; font.weight: Font.Black }
                        Text { text: controller.actionLabel; color: "white"; font.pixelSize: 28; font.weight: Font.Bold; Layout.fillWidth: true; elide: Text.ElideRight }
                        Text { text: controller.remainingText; color: "white"; font.pixelSize: 30; font.weight: Font.Black; font.family: "Consolas"; Layout.fillWidth: true; elide: Text.ElideRight }
                        Text { text: controller.powerActionProgressText; color: "#DCE8FF"; font.pixelSize: 11; Layout.fillWidth: true; elide: Text.ElideRight }
                        Text { text: mainWindow.formatPowerActionStepSummary(controller.powerActionStepSummaryText); color: "#C7D5EA"; font.pixelSize: 10; Layout.fillWidth: true; elide: Text.ElideRight }
                        GridLayout {
                            id: currentTaskActions
                            Layout.fillWidth: true
                            columns: 2
                            rowSpacing: 6
                            columnSpacing: 8
                            NeonButton { Layout.fillWidth: true; Layout.preferredHeight: 28; compact: true; text: "延后 5 分钟"; enabled: controller.status === "running"; onClicked: controller.snoozeMinutes(5) }
                            NeonButton { Layout.fillWidth: true; Layout.preferredHeight: 28; compact: true; text: "延后 10 分钟"; enabled: controller.status === "running"; onClicked: controller.snoozeMinutes(10) }
                            NeonButton { Layout.fillWidth: true; Layout.preferredHeight: 28; compact: true; variant: "secondary"; text: "跳过等待"; visible: controller.canSkipCloseAppsWait; onClicked: controller.skipCloseAppsWait() }
                            NeonButton { Layout.fillWidth: true; Layout.preferredHeight: 28; compact: true; variant: "quietDanger"; text: "立即执行"; enabled: !controller.powerActionInProgress; onClicked: confirmDialog.open() }
                        }
                    }
                }

                Item {
                    id: rightStatusPanel
                    x: overviewWorkbench.contentLeftWidth + overviewWorkbench.overviewGap
                    y: overviewWorkbench.contentRowY
                    width: overviewWorkbench.contentRightWidth
                    height: overviewWorkbench.contentRowHeight

                    NeonCard {
                        id: overviewActionPanel
                        x: 0
                        y: 0
                        width: parent.width
                        height: 106
                        radius: 28
                        cardColor: Theme.blogGlassPanel
                        cardBorderColor: Theme.blogCardBorder
                        clip: true

                        Image { id: scheduleBannerCard; anchors.fill: parent; source: "assets/blog-banner-cover.png"; fillMode: Image.PreserveAspectCrop; smooth: true; mipmap: true; opacity: 0.86 }
                        Rectangle { anchors.fill: parent; color: "#52000000" }

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 14
                            spacing: 6
                            RowLayout { Layout.fillWidth: true; Text { Layout.fillWidth: true; text: "电源动作"; color: "white"; font.pixelSize: 22; font.weight: Font.Bold } Text { text: "Action Deck"; color: Theme.commandRose; font.pixelSize: 12; font.weight: Font.Black } }
                            GridLayout {
                                Layout.fillWidth: true
                                columns: 6
                                rowSpacing: 6
                                columnSpacing: 6
                                ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 40; actionKey: "shutdown"; actionLabel: "关机"; actionSub: "模拟" }
                                ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 40; actionKey: "sleep"; actionLabel: "睡眠"; actionSub: "休息" }
                                ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 40; actionKey: "hibernate"; actionLabel: "休眠"; actionSub: "保存" }
                                ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 40; actionKey: "restart"; actionLabel: "重启"; actionSub: "刷新" }
                                ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 40; actionKey: "logoff"; actionLabel: "注销"; actionSub: "账户" }
                                ActionTile { Layout.fillWidth: true; Layout.preferredHeight: 40; actionKey: "lock"; actionLabel: "锁定"; actionSub: "屏幕" }
                            }
                        }
                    }

                    readonly property int lowerY: overviewActionPanel.height + overviewWorkbench.overviewGap
                    readonly property int lowerHeight: height - lowerY
                    readonly property int statusCardWidth: Math.round((width - overviewWorkbench.overviewGap * 2) * 0.42)
                    readonly property int activityCardWidth: Math.round((width - overviewWorkbench.overviewGap * 2) * 0.36)

                    NeonCard {
                        id: overviewStatusSummary
                        x: 0
                        y: parent.lowerY
                        width: parent.statusCardWidth
                        height: parent.lowerHeight
                        radius: 28
                        cardColor: Theme.blogGlassPanel
                        cardBorderColor: Theme.blogCardBorder
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 3
                            Text { text: "运行概览"; color: Theme.textPrimary; font.pixelSize: 17; font.weight: Font.Bold }
                            Text { Layout.fillWidth: true; text: controller.dryRun ? "安全验证中" : "真实执行模式"; color: controller.dryRun ? Theme.commandEmerald : Theme.danger; font.pixelSize: 13; font.weight: Font.Bold; elide: Text.ElideRight }
                            Text { Layout.fillWidth: true; text: "动作：" + controller.actionLabel; color: Theme.textSecondary; font.pixelSize: 11; elide: Text.ElideRight }
                            Text { Layout.fillWidth: true; text: "队列数量：" + String(mainWindow.queueRowModel.length); color: Theme.textSecondary; font.pixelSize: 11; elide: Text.ElideRight }
                            Text { Layout.fillWidth: true; text: (controller.processTriggerActive || controller.networkTriggerActive) ? "触发器：已启用" : "触发器：未启用"; color: Theme.textSecondary; font.pixelSize: 11; elide: Text.ElideRight }
                        }
                    }

                    NeonCard {
                        id: overviewRecentActivity
                        x: overviewStatusSummary.width + overviewWorkbench.overviewGap
                        y: parent.lowerY
                        width: parent.activityCardWidth
                        height: parent.lowerHeight
                        radius: 28
                        cardColor: Theme.blogGlassPanel
                        cardBorderColor: Theme.blogCardBorder
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 14
                            spacing: 5
                            Text { text: "最近活动"; color: Theme.textPrimary; font.pixelSize: 18; font.weight: Font.Bold }
                            Text { text: "后台托盘"; color: Theme.textSecondary; font.pixelSize: 12; font.weight: Font.Bold }
                            Text { Layout.fillWidth: true; text: "托盘可用时关闭窗口会隐藏到后台。"; color: Theme.commandCool; font.pixelSize: 12; wrapMode: Text.WordWrap; maximumLineCount: 2 }
                            Text { Layout.fillWidth: true; Layout.fillHeight: true; text: controller.logText; color: Theme.textSecondary; font.pixelSize: 11; wrapMode: Text.WordWrap; elide: Text.ElideRight }
                        }
                    }

                    NeonCard {
                        id: moodModeCard
                        x: overviewRecentActivity.x + overviewRecentActivity.width + overviewWorkbench.overviewGap
                        y: parent.lowerY
                        width: parent.width - x
                        height: parent.lowerHeight
                        radius: 28
                        cardColor: Theme.blogGlassPanel
                        cardBorderColor: Theme.blogCardBorder
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 4
                            Rectangle { Layout.alignment: Qt.AlignHCenter; Layout.preferredWidth: 48; Layout.preferredHeight: 48; radius: 24; color: "#33343D6D"; Text { anchors.centerIn: parent; text: "✓"; color: Theme.commandWarm; font.pixelSize: 25 } }
                            Text { Layout.fillWidth: true; text: controller.dryRun ? "夜间安全" : "真实执行"; color: Theme.textPrimary; font.pixelSize: 17; font.weight: Font.Bold; horizontalAlignment: Text.AlignHCenter; fontSizeMode: Text.HorizontalFit; minimumPixelSize: 12 }
                            Text { Layout.fillWidth: true; text: controller.dryRun ? "验证模式不会真实关机" : "真实模式会执行系统动作"; color: Theme.textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap; maximumLineCount: 2; horizontalAlignment: Text.AlignHCenter }
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
