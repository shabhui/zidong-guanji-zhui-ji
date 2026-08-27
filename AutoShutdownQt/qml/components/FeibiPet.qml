import QtQuick
import QtQuick.Layouts
import QtMultimedia
import ".."

// 桌宠「菲比」：从 Main.qml 抽出的自包含组件。
// 对外 API：
//   active            —— 是否处于活动页（父级传 blogHomeDashboard.visible），停用时暂停动画。
//   playFeibiVoice(f) —— 播放 assets/feibi/sounds/<f> 语音（外部快捷按钮调用，f 为裸文件名）。
// 依赖上下文属性 controller（feibiTaskSeconds/feibiTaskActionLabel/powerActionInProgress 等）。
Item {
    id: feibiPetStage

    property bool active: true
    property real stageScale: 1.0

    property string feibiAction: "idle"
    property bool feibiPaused: false
    property bool feibiManualMode: false
    property bool feibiVoiceActive: false
    property bool feibiVoicePaused: false
    property int feibiAmbientStep: 0
    property int feibiInteractionStep: 0
    property string feibiMood: "happy"
    property int feibiHunger: 12
    property string feibiTaskPhase: "idle"
    property string feibiSpeech: ""
    property real feibiOffsetX: 0
    property real feibiOffsetY: 0
    property bool feibiDragging: false
    property bool feibiBlink: false
    property bool feibiWavePhase: false
    readonly property bool feibiTaskActive: feibiTaskPhase === "urgent" || feibiTaskPhase === "farewell"

    x: (parent ? parent.width - width - 8 : 0) + feibiOffsetX
    y: 8 + feibiOffsetY
    width: Math.round(172 * feibiPetStage.stageScale)
    height: Math.round(170 * feibiPetStage.stageScale)
    z: 2
    Behavior on x { enabled: !feibiPetStage.feibiDragging; NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
    Behavior on y { enabled: !feibiPetStage.feibiDragging; NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
    scale: feibiPetStage.feibiDragging ? 1.06 : 1.0
    Behavior on scale { NumberAnimation { duration: 160; easing.type: Easing.OutBack } }

    function _voiceUrl(sound) {
        return Qt.resolvedUrl("../assets/feibi/sounds/" + sound)
    }

    function setFeibiAction(actionName, autoReturnMs, manualMode) {
        feibiAction = actionName
        feibiReturnTimer.stop()
        if (manualMode === true) {
            feibiPetStage.feibiManualMode = true
        } else if (autoReturnMs > 0) {
            feibiPetStage.feibiManualMode = false
        }
        if (autoReturnMs > 0) {
            feibiReturnTimer.interval = autoReturnMs
            feibiReturnTimer.restart()
        }
    }

    function stopFeibiVoice(resetAction) {
        if (resetAction !== false) {
            feibiReturnTimer.stop()
        }
        feibiVoicePlayer.stop()
        feibiVoicePlayer.source = ""
        feibiPetStage.feibiVoiceActive = false
        feibiPetStage.feibiVoicePaused = false
        feibiPetStage.feibiPaused = false
        if (resetAction !== false && !feibiPetStage.feibiTaskActive) {
            feibiPetStage.feibiManualMode = false
            feibiPetStage.setFeibiAction("idle", 0, false)
        }
    }

    function _startFeibiVoice(sound) {
        feibiPetStage.stopFeibiVoice(false)
        feibiVoicePlayer.source = _voiceUrl(sound)
        feibiVoicePlayer.play()
    }

    function playFeibiVoice(sound) {
        feibiPetStage.feibiPaused = false
        feibiPetStage.feibiManualMode = false
        feibiPetStage._startFeibiVoice(sound)
        setFeibiAction("talk", 5200, false)
    }

    function toggleFeibiVoice() {
        if (feibiPetStage.feibiVoiceActive || feibiPetStage.feibiVoicePaused
                || feibiVoicePlayer.playbackState === MediaPlayer.PausedState) {
            feibiPetStage.stopFeibiVoice(true)
            return
        }
        feibiPetStage.patFeibi()
    }

    function toggleFeibiPaused() {
        if (feibiPetStage.feibiVoicePaused
                || feibiVoicePlayer.playbackState === MediaPlayer.PausedState) {
            feibiPetStage.feibiPaused = false
            feibiPetStage.feibiVoicePaused = false
            feibiVoicePlayer.play()
            return
        }
        if (feibiPetStage.feibiVoiceActive) {
            feibiPetStage.feibiPaused = true
            feibiPetStage.feibiVoicePaused = true
            feibiVoicePlayer.pause()
            return
        }
        feibiPetStage.feibiPaused = !feibiPetStage.feibiPaused
    }

    function interactWithFeibi() {
        feibiPetStage.stopFeibiVoice(false)
        feibiPetStage.feibiPaused = false
        feibiPetStage.feibiManualMode = true
        feibiPetStage.feibiInteractionStep = (feibiPetStage.feibiInteractionStep + 1) % 4
        var actions = ["push", "eating", "sleep", "talk"]
        var actionName = actions[feibiPetStage.feibiInteractionStep]
        feibiPetStage.setFeibiAction(actionName, 0, true)
        if (actionName === "talk") {
            feibiPetStage._startFeibiVoice("feibi-chuubi.mp3")
        }
    }

    function refreshFeibiMood() {
        if (feibiPetStage.feibiTaskActive) return
        if (feibiPetStage.feibiHunger >= 68) {
            feibiPetStage.feibiMood = "hungry"
        } else if (feibiPetStage.feibiAction === "sleep") {
            feibiPetStage.feibiMood = "sleepy"
        } else if (feibiPetStage.feibiHunger <= 30) {
            feibiPetStage.feibiMood = "happy"
        } else {
            feibiPetStage.feibiMood = "normal"
        }
    }

    function feibiMoodText() {
        if (feibiPetStage.feibiMood === "hungry") return "肚子饿了…喂喂我嘛"
        if (feibiPetStage.feibiMood === "sleepy") return "有点困了 zzz"
        if (feibiPetStage.feibiMood === "happy") return "心情不错！"
        return "菲比在你身边"
    }

    function feedFeibi() {
        feibiPetStage.feibiPaused = false
        feibiPetStage.feibiHunger = Math.max(0, feibiPetStage.feibiHunger - 46)
        feibiPetStage.feibiMood = "happy"
        feibiPetStage.setFeibiAction("eating", 3200, false)
        feibiPetStage._startFeibiVoice("feibi-chuubi.mp3")
    }

    function patFeibi() {
        if (feibiPetStage.feibiTaskActive) {
            feibiPetStage.feibiTaskChirp("feibi-call.mp3")
            return
        }
        if (feibiPetStage.feibiMood === "hungry") {
            feibiPetStage.feedFeibi()
            return
        }
        feibiPetStage.feibiPaused = false
        feibiPetStage.feibiMood = "happy"
        feibiPetStage.feibiHunger = Math.min(100, feibiPetStage.feibiHunger + 4)
        feibiPetStage.setFeibiAction("wave", 2200, false)
        feibiPetStage._startFeibiVoice("feibi-call.mp3")
    }

    function feibiTaskChirp(sound) {
        feibiPetStage._startFeibiVoice(sound)
    }

    function feibiFormatCountdown(secs) {
        if (secs < 0) return ""
        function pad(n) { return n < 10 ? "0" + n : "" + n }
        var h = Math.floor(secs / 3600)
        var m = Math.floor((secs % 3600) / 60)
        var s = secs % 60
        if (h > 0) return pad(h) + ":" + pad(m) + ":" + pad(s)
        return pad(m) + ":" + pad(s)
    }

    function syncFeibiWithTask() {
        var secs = controller.feibiTaskSeconds
        var label = controller.feibiTaskActionLabel !== "" ? controller.feibiTaskActionLabel : controller.actionLabel
        var newPhase = "idle"
        if (controller.powerActionInProgress) {
            newPhase = "farewell"
        } else if (secs >= 0 && secs <= 60) {
            newPhase = "urgent"
        } else if (secs > 60) {
            newPhase = "watching"
        }

        if (newPhase === "farewell") {
            feibiPetStage.feibiSpeech = "要" + label + "啦，拜拜~"
        } else if (newPhase === "urgent") {
            feibiPetStage.feibiSpeech = "还有 " + feibiPetStage.feibiFormatCountdown(secs) + " 就" + label + "！"
        } else if (newPhase === "watching") {
            feibiPetStage.feibiSpeech = label + " · 倒计时 " + feibiPetStage.feibiFormatCountdown(secs)
        } else {
            feibiPetStage.feibiSpeech = ""
        }

        if (newPhase !== feibiPetStage.feibiTaskPhase) {
            feibiPetStage.feibiTaskPhase = newPhase
            if (newPhase === "urgent" || newPhase === "farewell") {
                feibiPetStage.feibiManualMode = false
                feibiPetStage.feibiPaused = false
            }
            if (newPhase === "farewell") {
                feibiPetStage.setFeibiAction("sleep", 0, false)
                feibiPetStage.feibiTaskChirp("time.mp3")
            } else if (newPhase === "urgent") {
                feibiPetStage.setFeibiAction("push", 0, false)
                feibiPetStage.feibiTaskChirp("feibi-call.mp3")
            } else if (newPhase === "watching") {
                feibiPetStage.refreshFeibiMood()
            } else {
                feibiPetStage.setFeibiAction("idle", 0, false)
                feibiPetStage.refreshFeibiMood()
            }
        }
    }

    function clampFeibiOffsetX(value) {
        if (!feibiPetStage.parent) return value
        var base = feibiPetStage.parent.width - feibiPetStage.width - 8
        var minOff = -base
        var maxOff = 8
        if (maxOff < minOff) maxOff = minOff
        return Math.max(minOff, Math.min(maxOff, value))
    }

    function clampFeibiOffsetY(value) {
        if (!feibiPetStage.parent) return value
        var minOff = -8
        var maxOff = feibiPetStage.parent.height - feibiPetStage.height - 8
        if (maxOff < minOff) maxOff = minOff
        return Math.max(minOff, Math.min(maxOff, value))
    }

    AudioOutput { id: feibiVoiceOutput; volume: 0.58 }

    MediaPlayer {
        id: feibiVoicePlayer
        audioOutput: feibiVoiceOutput
        onPlaybackStateChanged: {
            feibiPetStage.feibiVoiceActive = playbackState === MediaPlayer.PlayingState
            if (playbackState === MediaPlayer.PlayingState) {
                feibiPetStage.feibiVoicePaused = false
            } else if (playbackState === MediaPlayer.StoppedState && !feibiPetStage.feibiVoicePaused) {
                feibiPetStage.feibiVoicePaused = false
            }
            if (playbackState === MediaPlayer.StoppedState && feibiPetStage.feibiAction === "talk" && !feibiPetStage.feibiManualMode && !feibiReturnTimer.running) {
                feibiPetStage.setFeibiAction("idle", 0)
            }
        }
    }

    onActiveChanged: {
        if (!active) {
            feibiPetStage.stopFeibiVoice(true)
        }
    }

    Timer {
        id: feibiReturnTimer
        repeat: false
        onTriggered: feibiPetStage.setFeibiAction("idle", 0)
    }

    Timer {
        id: feibiAmbientActionTimer
        running: feibiPetStage.active && !feibiPetStage.feibiPaused
        repeat: true
        interval: 6800
        onTriggered: {
            if (feibiPetStage.feibiTaskActive) return
            if (feibiPetStage.feibiPaused || feibiPetStage.feibiManualMode || feibiPetStage.feibiVoiceActive) return
            feibiPetStage.feibiHunger = Math.min(100, feibiPetStage.feibiHunger + 6)
            feibiPetStage.refreshFeibiMood()
            feibiPetStage.feibiAmbientStep = (feibiPetStage.feibiAmbientStep + 1) % 4
            if (feibiPetStage.feibiMood === "hungry" && feibiPetStage.feibiHunger >= 80) {
                feibiPetStage.feibiHunger = Math.max(30, feibiPetStage.feibiHunger - 18)
                feibiPetStage.setFeibiAction("eating", 5200, false)
            } else if (feibiPetStage.feibiAmbientStep === 1) {
                feibiPetStage.setFeibiAction("push", 4200, false)
            } else if (feibiPetStage.feibiAmbientStep === 2) {
                feibiPetStage.setFeibiAction("eating", 5200, false)
            } else if (feibiPetStage.feibiAmbientStep === 3) {
                feibiPetStage.setFeibiAction("sleep", 6200, false)
            } else {
                feibiPetStage.setFeibiAction("idle", 0, false)
            }
        }
    }

    Connections {
        target: controller
        function onFeibiTaskChanged() {
            feibiPetStage.syncFeibiWithTask()
        }
        function onPowerActionProgressChanged() {
            feibiPetStage.syncFeibiWithTask()
        }
        function onTaskQueueChanged() {
            feibiPetStage.syncFeibiWithTask()
        }
        function onReminderChanged() {
            if (controller.reminderDialogTitle !== "" && controller.status === "running") {
                feibiPetStage.feibiTaskChirp("time.mp3")
            }
        }
    }

    Component.onCompleted: {
        feibiPetStage.syncFeibiWithTask()
        feibiGreetTimer.start()
    }

    Timer {
        id: feibiGreetTimer
        interval: 450
        repeat: false
        onTriggered: if (!feibiPetStage.feibiTaskActive) feibiPetStage.setFeibiAction("wave", 2200, false)
    }

    Timer {
        id: feibiBlinkTimer
        running: feibiPetStage.active && !feibiPetStage.feibiPaused
        interval: 3400
        repeat: true
        onTriggered: {
            if (feibiPetStage.feibiAction === "sleep" || feibiPetStage.feibiAction === "wave" || feibiPetStage.feibiAction === "push") return
            feibiPetStage.feibiBlink = true
            feibiBlinkOffTimer.restart()
        }
    }

    Timer {
        id: feibiBlinkOffTimer
        interval: 150
        repeat: false
        onTriggered: feibiPetStage.feibiBlink = false
    }

    Timer {
        id: feibiWaveTimer
        running: feibiPetStage.active && feibiPetStage.feibiAction === "wave"
        interval: 240
        repeat: true
        onTriggered: feibiPetStage.feibiWavePhase = !feibiPetStage.feibiWavePhase
        onRunningChanged: if (!running) feibiPetStage.feibiWavePhase = false
    }

    Rectangle {
        id: feibiStageHalo
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: 22
        width: Math.round(128 * feibiPetStage.stageScale)
        height: Math.round(128 * feibiPetStage.stageScale)
        radius: width / 2
        color: "#1828D7FF"
        border.color: feibiPetStage.feibiTaskPhase === "urgent" ? Theme.danger
                      : feibiPetStage.feibiTaskPhase === "farewell" ? Theme.animeVioletGlow
                      : feibiPetStage.feibiMood === "hungry" ? Theme.warning
                      : feibiPetStage.feibiVoiceActive ? Theme.animeSakura
                      : Theme.animeCyanGlow
        border.width: 1
        opacity: feibiPetStage.feibiVoiceActive ? 1.0 : 0.76
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
        anchors.leftMargin: Math.round(4 * feibiPetStage.stageScale)
        anchors.topMargin: 0
        width: Math.round(92 * feibiPetStage.stageScale)
        height: Math.round(30 * feibiPetStage.stageScale)
        radius: height / 2
        color: "#D01A243A"
        border.color: feibiPetStage.feibiVoiceActive ? Theme.animeSakura : Theme.animeCyanGlow
        border.width: 1
        opacity: (feibiPetStage.feibiSpeech !== "" || feibiPetStage.feibiMood === "hungry" || feibiStageMouse.containsMouse) ? 0.0 : (feibiPetStage.feibiVoiceActive ? 0.85 : 0.6)
        Behavior on opacity { NumberAnimation { duration: 200; easing.type: Easing.InOutSine } }
        Text {
            anchors.centerIn: parent
            text: feibiPetStage.feibiAction === "talk" ? "菲比播报中"
                  : feibiPetStage.feibiAction === "sleep" ? "休眠巡逻"
                  : feibiPetStage.feibiAction === "eating" ? "补充能量"
                  : feibiPetStage.feibiAction === "push" ? "别偷懒"
                  : "菲比待命"
            color: Theme.textPrimary
            font.pixelSize: Math.round(10 * feibiPetStage.stageScale)
            font.weight: Font.Bold
            maximumLineCount: 1
        }
    }

    Rectangle {
        id: feibiTaskBubble
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: 2
        width: Math.min(parent.width - 6, Math.max(96, feibiTaskBubbleLabel.implicitWidth + 24))
        height: 32
        radius: 15
        color: "#E60E1626"
        border.width: 1
        border.color: feibiPetStage.feibiTaskPhase === "urgent" ? Theme.danger
                      : feibiPetStage.feibiTaskPhase === "farewell" ? Theme.animeVioletGlow
                      : feibiPetStage.feibiMood === "hungry" ? Theme.warning
                      : feibiPetStage.feibiVoiceActive ? Theme.animeSakura
                      : Theme.animeCyanGlow
        opacity: (feibiPetStage.feibiSpeech !== "" || feibiPetStage.feibiMood === "hungry" || feibiStageMouse.containsMouse) ? 0.98 : 0.0
        z: 6
        Behavior on opacity { NumberAnimation { duration: 220; easing.type: Easing.InOutSine } }
        Behavior on width { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }

        Rectangle {
            id: feibiTaskBubbleTail
            width: 11
            height: 11
            radius: 2
            color: parent.color
            border.width: 1
            border.color: parent.border.color
            rotation: 45
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.bottom
            anchors.topMargin: -6
            z: -1
        }

        Text {
            id: feibiTaskBubbleLabel
            anchors.centerIn: parent
            width: parent.width - 18
            text: feibiPetStage.feibiSpeech !== "" ? feibiPetStage.feibiSpeech : feibiPetStage.feibiMoodText()
            color: feibiPetStage.feibiTaskPhase === "urgent" ? "#FFE1EA" : Theme.textPrimary
            font.pixelSize: 10
            font.weight: Font.Bold
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
            maximumLineCount: 1
        }

        SequentialAnimation on scale {
            running: feibiPetStage.active && feibiPetStage.feibiTaskPhase === "urgent"
            loops: Animation.Infinite
            NumberAnimation { from: 1.0; to: 1.07; duration: 420; easing.type: Easing.InOutSine }
            NumberAnimation { from: 1.07; to: 1.0; duration: 420; easing.type: Easing.InOutSine }
        }
    }

    Rectangle {
        id: feibiStateBadge
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.rightMargin: Math.round(16 * feibiPetStage.stageScale)
        anchors.topMargin: Math.round(12 * feibiPetStage.stageScale)
        width: Math.round(18 * feibiPetStage.stageScale)
        height: Math.round(18 * feibiPetStage.stageScale)
        radius: width / 2
        color: feibiPetStage.feibiTaskPhase === "urgent" ? Theme.danger
               : feibiPetStage.feibiTaskPhase === "farewell" ? Theme.animeVioletGlow
               : feibiPetStage.feibiVoiceActive ? Theme.animeSakura
               : Theme.commandEmerald
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
        width: Math.round(86 * feibiPetStage.stageScale)
        height: Math.round(18 * feibiPetStage.stageScale)
        radius: height / 2
        color: "#66000000"
        opacity: 0.46 + feibiSpriteFloatTransform.y / 120
        scale: 1.0 + feibiSpriteFloatTransform.y / 46
        SequentialAnimation on width {
            loops: Animation.Infinite
            NumberAnimation { from: 76; to: 98; duration: 1800; easing.type: Easing.InOutSine }
            NumberAnimation { from: 98; to: 76; duration: 1800; easing.type: Easing.InOutSine }
        }
    }

    Image {
        id: feibiDesktopPetSprite
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: feibiControlDock.top
        anchors.bottomMargin: -2
        width: Math.round(152 * feibiPetStage.stageScale)
        height: Math.round(160 * feibiPetStage.stageScale)
        source: feibiPetStage.feibiAction === "wave" ? (feibiPetStage.feibiWavePhase ? "../assets/feibi/frames/wave.png" : "../assets/feibi/frames/idle_open.png")
                : feibiPetStage.feibiAction === "push" ? "../assets/feibi/frames/angry.png"
                : feibiPetStage.feibiAction === "sleep" ? "../assets/feibi/frames/idle_closed.png"
                : feibiPetStage.feibiBlink ? "../assets/feibi/frames/idle_closed.png"
                : "../assets/feibi/frames/idle_open.png"
        fillMode: Image.PreserveAspectFit
        mipmap: true
        smooth: true
        opacity: 0.99
        onSourceChanged: if (!feibiPetStage.feibiBlink && feibiPetStage.feibiAction !== "wave") feibiSpritePop.restart()
        SequentialAnimation {
            id: feibiSpritePop
            NumberAnimation { target: feibiDesktopPetSprite; property: "scale"; from: 0.84; to: 1.0; duration: 280; easing.type: Easing.OutBack }
        }
        transform: [
            Scale {
                id: feibiBreatheScale
                origin.x: feibiDesktopPetSprite.width / 2
                origin.y: feibiDesktopPetSprite.height
            },
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
            running: feibiPetStage.active && !feibiPetStage.feibiPaused
            loops: Animation.Infinite
            NumberAnimation { target: feibiSpriteFloatTransform; property: "y"; from: 0; to: -7; duration: 1900; easing.type: Easing.InOutSine }
            NumberAnimation { target: feibiSpriteFloatTransform; property: "y"; from: -7; to: 0; duration: 1900; easing.type: Easing.InOutSine }
        }
        SequentialAnimation {
            running: feibiPetStage.active && !feibiPetStage.feibiPaused
            loops: Animation.Infinite
            NumberAnimation { target: feibiSpriteTiltTransform; property: "angle"; from: -1.0; to: 1.0; duration: 2400; easing.type: Easing.InOutSine }
            NumberAnimation { target: feibiSpriteTiltTransform; property: "angle"; from: 1.0; to: -1.0; duration: 2400; easing.type: Easing.InOutSine }
        }
        SequentialAnimation {
            running: feibiPetStage.active && !feibiPetStage.feibiPaused
            loops: Animation.Infinite
            ParallelAnimation {
                NumberAnimation { target: feibiBreatheScale; property: "yScale"; from: 1.0; to: 1.04; duration: 1500; easing.type: Easing.InOutSine }
                NumberAnimation { target: feibiBreatheScale; property: "xScale"; from: 1.0; to: 0.985; duration: 1500; easing.type: Easing.InOutSine }
            }
            ParallelAnimation {
                NumberAnimation { target: feibiBreatheScale; property: "yScale"; from: 1.04; to: 1.0; duration: 1500; easing.type: Easing.InOutSine }
                NumberAnimation { target: feibiBreatheScale; property: "xScale"; from: 0.985; to: 1.0; duration: 1500; easing.type: Easing.InOutSine }
            }
        }
    }

    Item {
        id: feibiControlDock
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        width: Math.round(132 * feibiPetStage.stageScale)
        height: Math.round(28 * feibiPetStage.stageScale)
        z: 5

        Row {
            anchors.fill: parent
            spacing: 6

            Rectangle {
                id: feibiPlayButton
                width: Math.round(40 * feibiPetStage.stageScale)
                height: Math.round(26 * feibiPetStage.stageScale)
                radius: height / 2
                color: "#3328D7FF"
                border.color: Theme.animeCyanGlow
                Text { anchors.centerIn: parent; text: feibiPetStage.feibiVoiceActive || feibiPetStage.feibiVoicePaused ? "停止" : "播放"; color: Theme.textPrimary; font.pixelSize: Math.round(10 * feibiPetStage.stageScale); font.weight: Font.Bold }
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: feibiPetStage.toggleFeibiVoice()
                }
            }
            Rectangle {
                id: feibiPauseButton
                width: Math.round(40 * feibiPetStage.stageScale)
                height: Math.round(26 * feibiPetStage.stageScale)
                radius: height / 2
                color: feibiPetStage.feibiPaused ? "#4462F6B5" : "#3346F1A8"
                border.color: feibiPetStage.feibiPaused ? Theme.commandEmerald : Theme.borderStrong
                Text { anchors.centerIn: parent; text: feibiPetStage.feibiVoicePaused || feibiPetStage.feibiPaused ? "继续" : "暂停"; color: Theme.textPrimary; font.pixelSize: Math.round(10 * feibiPetStage.stageScale); font.weight: Font.Bold }
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: feibiPetStage.toggleFeibiPaused()
                }
            }
            Rectangle {
                id: feibiInteractButton
                width: Math.round(40 * feibiPetStage.stageScale)
                height: Math.round(26 * feibiPetStage.stageScale)
                radius: height / 2
                color: "#33FF8ACF"
                border.color: Theme.animeSakura
                Text { anchors.centerIn: parent; text: "互动"; color: Theme.textPrimary; font.pixelSize: Math.round(10 * feibiPetStage.stageScale); font.weight: Font.Bold }
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: feibiPetStage.interactWithFeibi()
                }
            }
        }
    }

    MouseArea {
        id: feibiStageMouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: feibiPetStage.feibiDragging ? Qt.ClosedHandCursor : Qt.PointingHandCursor
        property real grabX: 0
        property real grabY: 0
        property real grabOffX: 0
        property real grabOffY: 0
        property bool moved: false
        onPressed: (mouse) => {
            var p = mapToItem(feibiPetStage.parent, mouse.x, mouse.y)
            grabX = p.x
            grabY = p.y
            grabOffX = feibiPetStage.feibiOffsetX
            grabOffY = feibiPetStage.feibiOffsetY
            moved = false
        }
        onPositionChanged: (mouse) => {
            if (!pressed) return
            var p = mapToItem(feibiPetStage.parent, mouse.x, mouse.y)
            var dx = p.x - grabX
            var dy = p.y - grabY
            if (!moved && (Math.abs(dx) + Math.abs(dy)) > 6) {
                moved = true
                feibiPetStage.feibiDragging = true
            }
            if (moved) {
                feibiPetStage.feibiOffsetX = feibiPetStage.clampFeibiOffsetX(grabOffX + dx)
                feibiPetStage.feibiOffsetY = feibiPetStage.clampFeibiOffsetY(grabOffY + dy)
            }
        }
        onReleased: feibiPetStage.feibiDragging = false
        onCanceled: feibiPetStage.feibiDragging = false
        onClicked: {
            if (moved) {
                moved = false
                return
            }
            feibiPetStage.toggleFeibiVoice()
        }
        onEntered: {
            if (!feibiPetStage.feibiVoiceActive && !feibiPetStage.feibiVoicePaused) {
                feibiPetStage.setFeibiAction("push", 1600)
            }
        }
    }

    Row {
        id: feibiVoiceEqualizer
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: feibiControlDock.top
        anchors.bottomMargin: 2
        spacing: 4
        opacity: feibiPetStage.feibiVoiceActive ? 0.95 : 0.0
        Repeater {
            model: 5
            Rectangle {
                width: 4
                height: 8 + index * 2
                radius: 2
                color: index % 2 === 0 ? Theme.animeCyanGlow : Theme.animeSakura
                SequentialAnimation on height {
                    running: feibiPetStage.active && feibiPetStage.feibiVoiceActive
                    loops: Animation.Infinite
                    NumberAnimation { to: 22 - index * 2; duration: 260 + index * 40; easing.type: Easing.InOutSine }
                    NumberAnimation { to: 8 + index * 2; duration: 300 + index * 35; easing.type: Easing.InOutSine }
                }
            }
        }
    }
}
