from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
QML = ROOT / "AutoShutdownQt" / "qml"
MAIN_QML = QML / "Main.qml"
CONFIRM_DIALOG_QML = QML / "components" / "ConfirmDialog.qml"
NEON_BUTTON_QML = QML / "components" / "NeonButton.qml"


class E5E8ButtonRegressionTest(unittest.TestCase):
    def test_main_uses_neon_buttons_instead_of_default_fusion_buttons(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertTrue(NEON_BUTTON_QML.exists(), "NeonButton.qml should define the e5e8 glass button skin")
        self.assertNotRegex(main, r"(?m)^\s*Button\s*\{", "Main.qml should not use unskinned Qt Fusion Button controls")
        self.assertGreaterEqual(main.count("NeonButton {"), 11, "Main.qml should skin title, hero, preset, timer, and task buttons")

    def test_quick_countdown_presets_are_two_by_two_neon_chips(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        quick_section_match = re.search(r'Text \{ text: "快捷倒计时".*?\n\s*}\n\s*</?[^\n]*', main, re.S)
        self.assertIn('Text { text: "快捷倒计时"', main)
        quick_index = main.index('Text { text: "快捷倒计时"')
        current_config_index = main.index('Text { text: "当前配置"', quick_index)
        quick_section = main[quick_index:current_config_index]

        self.assertIn("GridLayout {", quick_section)
        self.assertIn("columns: 2", quick_section)
        self.assertEqual(quick_section.count("NeonButton {"), 4)
        for label in ("15 分钟", "30 分钟", "1 小时", "2 小时"):
            self.assertIn(f'text: "{label}"', quick_section)
        self.assertGreaterEqual(quick_section.count("Layout.preferredHeight: 38"), 4)

    def test_confirm_dialog_uses_custom_neon_footer_buttons(self):
        dialog = CONFIRM_DIALOG_QML.read_text(encoding="utf-8")

        self.assertNotIn("standardButtons: Dialog.Ok | Dialog.Cancel", dialog)
        self.assertIn("standardButtons: Dialog.NoButton", dialog)
        self.assertGreaterEqual(dialog.count("NeonButton {"), 2)
        self.assertIn("onClicked: root.accept()", dialog)
        self.assertIn("onClicked: root.reject()", dialog)

    def test_overview_action_tiles_fit_default_window_height(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        title_index = main.index('Text { text: "电源动作"')
        power_index = main.rindex("NeonCard {", 0, title_index)
        status_panel_index = main.index("id: rightStatusPanel", power_index)
        power_section = main[power_index:status_panel_index]

        self.assertIn("Layout.preferredHeight: 252", main, "hero card should be compact enough for 720px windows")
        self.assertIn("Layout.preferredHeight: 150", main, "quick countdown row should fit chips while leaving room for action tiles")
        self.assertIn("Layout.preferredHeight: 170", power_section, "overview action card should reserve enough fixed space for two compact rows")
        self.assertIn("anchors.margins: 14", power_section, "overview action card needs compact margins")
        self.assertIn("rowSpacing: 6", power_section, "overview action grid needs compact row spacing")
        self.assertEqual(power_section.count("Layout.preferredHeight: 56"), 6, "overview action tiles need fixed compact heights")

    def test_core_mvp_pages_are_wired_to_controller(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        for template_key in ("shutdown_15", "shutdown_30", "sleep_60", "shutdown_2300"):
            self.assertIn(f'applyTaskTemplate("{template_key}")', main)
        for label in ("15 分钟后关机", "30 分钟后关机", "1 小时后睡眠", "今晚 23:00 关机"):
            self.assertIn(label, main)

        for snippet in (
            "controller.scriptEnabled",
            "controller.scriptPath",
            "controller.scriptTimeoutSeconds",
            "controller.testScript()",
            "controller.processName",
            "controller.processPollSeconds",
            "controller.startProcessTrigger()",
            "controller.stopProcessTrigger()",
            "controller.processTriggerStatus",
            "controller.logText",
        ):
            self.assertIn(snippet, main)

    def test_practical_enhancement_controls_are_wired_to_controller(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        for snippet in (
            "controller.networkDownloadThresholdKbps",
            "controller.networkUploadThresholdKbps",
            "controller.networkIdleSeconds",
            "controller.networkPollSeconds",
            "controller.networkSpeedText",
            "controller.networkTriggerStatus",
            "controller.startNetworkTrigger()",
            "controller.stopNetworkTrigger()",
            "controller.clearLogs()",
            "controller.exportLogs()",
            "controller.validateScriptPath()",
            "controller.openScriptFolder()",
        ):
            self.assertIn(snippet, main)
        for label in ("下载阈值", "上传阈值", "闲置秒数", "开始网络监控", "停止网络监控", "清空日志", "导出日志", "验证路径", "打开目录"):
            self.assertIn(label, main)

    def test_2_1_queue_and_repeat_controls_are_wired(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        for snippet in (
            "定时关机助手 v3.0",
            "v3.0 · 右侧状态栏",
            "controller.queueRowsJson",
            "JSON.parse(controller.queueRowsJson)",
            "controller.addFixedTimeTask(",
            "controller.setQueueTaskEnabled(",
            "controller.deleteQueueTask(",
            "controller.runQueueTaskDryRunCheck(",
            "repeatRuleCombo",
        ):
            self.assertIn(snippet, main)
        for label in ("任务队列", "重复规则", "仅一次", "每天", "工作日", "周末", "Dry-run 检查", "删除"):
            self.assertIn(label, main)

    def test_task_queue_list_model_refreshes_when_controller_queue_changes(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertIn("property var queueRowModel", main)
        self.assertIn("queueRowModel: queueRows()", main)
        self.assertIn("function onTaskQueueChanged()", main)
        self.assertIn("mainWindow.queueRowModel = mainWindow.queueRows()", main)
        self.assertIn("model: mainWindow.queueRowModel", main)
        self.assertNotIn("model: mainWindow.queueRows()", main)

    def test_neon_card_hover_layer_does_not_steal_child_clicks(self):
        card = (QML / "components" / "NeonCard.qml").read_text(encoding="utf-8")

        self.assertNotIn("MouseArea {", card)
        self.assertIn("HoverHandler {", card)

    def test_2_2_tray_copy_mentions_availability_and_explicit_quit(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertIn("托盘可用时关闭窗口会隐藏到后台", main)
        self.assertIn("托盘不可用时关闭窗口不会继续后台运行", main)
        self.assertIn("托盘菜单 Quit", main)
        self.assertIn("if (controller.trayAvailable && !trayCloseRequested)", main)
        self.assertIn("controller.minimizeToTray()", main)

    def test_main_starts_music_autoplay_after_qml_loads(self):
        main_py = (ROOT / "AutoShutdownQt" / "main.py").read_text(encoding="utf-8")

        self.assertIn("from music_service import MusicService", main_py)
        self.assertIn("from notification_service import NotificationService", main_py)
        self.assertIn("from startup_service import StartupService", main_py)
        self.assertIn("startup_service=StartupService()", main_py)
        self.assertIn("controller.notificationService = NotificationService(tray_service=tray_service, logger=controller._add_log)", main_py)
        self.assertNotIn("if controller.startMinimizedToTray and tray_service.available:", main_py)
        self.assertNotIn("window.hide()", main_py)
        self.assertIn("controller.startMusicAutoplay()", main_py)
        self.assertGreater(main_py.index("engine.load(str(main_qml))"), main_py.index("engine.rootContext().setContextProperty"))
        self.assertGreater(main_py.index("controller.startMusicAutoplay()"), main_py.index("if not engine.rootObjects():"))

    def test_main_sets_application_and_window_icon_from_packaged_image(self):
        main_py = (ROOT / "AutoShutdownQt" / "main.py").read_text(encoding="utf-8")
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertIn("from PySide6.QtGui import QIcon", main_py)
        self.assertIn('APP_ICON_PATH = Path(__file__).parent / "app_icon.png"', main_py)
        self.assertIn("app.setWindowIcon(QIcon(str(APP_ICON_PATH)))", main_py)
        self.assertIn("window.setIcon(QIcon(str(APP_ICON_PATH)))", main_py)
        self.assertIn("TrayService(controller, window, icon_path=APP_ICON_PATH", main_py)
        self.assertNotIn('icon: "../app_icon.png"', main)

    def test_title_bar_close_hides_to_tray_and_minimize_keeps_taskbar_behavior(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertNotIn("function minimizeWindow()", main)
        self.assertIn("mainWindow.showMinimized()", main)
        self.assertIn("onClicked: mainWindow.showMinimized()", main)
        self.assertIn("onClicked: mainWindow.close()", main)
        self.assertIn("if (controller.trayAvailable && !trayCloseRequested)", main)
        self.assertIn("controller.minimizeToTray()", main)

    def test_2_4_reminder_snooze_ui_is_wired_to_controller(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        for snippet in (
            "controller.reminderEnabled",
            "controller.reminderMinutesCsv",
            "controller.snoozeMinutesValue",
            "controller.reminderDialogTitle",
            "controller.reminderDialogBody",
            "controller.reminderDialogSnoozeText",
            "controller.snoozeCurrentTask()",
            "controller.cancelCurrentTask()",
            "function onReminderChanged()",
            "reminderDialog.open()",
        ):
            self.assertIn(snippet, main)
        for label in ("执行前提醒", "提醒分钟", "默认延后", "取消当前任务", "知道了"):
            self.assertIn(label, main)

    def test_2_5_background_experience_ui_is_wired_to_controller(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertIn("controller.windowsNotificationsEnabled", main)
        self.assertIn("controller.startWithWindows", main)
        self.assertIn("controller.taskHistoryLimit", main)
        self.assertIn("controller.historyRowsJson", main)
        self.assertIn("controller.clearHistory()", main)
        self.assertIn("controller.exportHistory()", main)
        self.assertIn("function historyRows()", main)
        self.assertIn("onHistoryChanged", main)
        self.assertNotIn("controller.startMinimizedToTray", main)
        for label in ("Windows 原生通知", "开机自动启动", "任务历史", "清空历史", "导出历史"):
            self.assertIn(label, main)
        self.assertNotIn("启动后最小化到托盘", main)

    def test_2_5_main_wires_notifications_startup_and_start_minimized(self):
        main_py = (ROOT / "AutoShutdownQt" / "main.py").read_text(encoding="utf-8")

        self.assertIn('app.setApplicationVersion("3.0")', main_py)
        self.assertIn("from notification_service import NotificationService", main_py)
        self.assertIn("from startup_service import StartupService", main_py)
        self.assertIn("controller.notificationService = NotificationService(tray_service=tray_service", main_py)
        self.assertIn("startup_service=StartupService()", main_py)
        self.assertNotIn("if controller.startMinimizedToTray and tray_service.available:", main_py)
        self.assertNotIn("window.hide()", main_py)

    def test_music_player_ui_is_wired_to_controller(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        for snippet in (
            "id: musicPlayerWindow",
            "controller.musicTitle",
            "controller.musicAvailable",
            "controller.musicPlaying",
            "controller.playMusic()",
            "controller.pauseMusic()",
            "controller.stopMusic()",
            "controller.setMusicVolume(",
            "controller.musicPlaybackMode",
            "controller.previousMusicTrack()",
            "controller.nextMusicTrack()",
            "controller.setMusicPlaybackMode(",
            "上一首",
            "下一首",
            "顺序播放",
            "列表循环",
            "单曲循环",
            "controller.musicAutoplayEnabled",
            "controller.musicTracksJson",
            "controller.musicCurrentIndex",
            "controller.musicPositionMs",
            "controller.musicDurationMs",
            "controller.musicPositionText",
            "controller.musicDurationText",
            "controller.chooseMusicFolder()",
            "controller.playMusicTrack(index)",
            "controller.seekMusic(",
            "FolderDialog",
            "选择音乐文件夹",
            "歌曲列表",
            "播放进度",
            "启动时自动播放音乐",
            "音乐播放器",
        ):
            self.assertIn(snippet, main)

    def test_2_3_right_status_panel_copy_is_chinese_and_visible(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        for snippet in (
            'title: "定时关机助手 v3.0"',
            'v3.0 · 右侧状态栏',
            'id: rightStatusPanel',
            '安全模式',
            'Dry-run 已开启',
            '下一任务',
            '队列数量',
            '触发器状态',
            '后台托盘',
            '最近活动',
        ):
            self.assertIn(snippet, main)

        self.assertNotIn('定时关机助手 v3.0 · Command Center', main)
        self.assertNotIn('Text { text: "Command Center"', main)
        self.assertNotIn('Text { text: "Next task"', main)
        self.assertNotIn('Text { text: "Active triggers"', main)
        self.assertNotIn('Text { text: "Queue health"', main)

    def test_2_3_status_panel_does_not_push_overview_below_fold(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertIn('id: rightStatusPanel', main)
        self.assertNotIn("id: safetyStrip", main)
        self.assertNotIn("id: commandCardsRow", main)
        self.assertNotIn("id: commandCenterScroll", main)
        self.assertIn('Text { text: "快捷倒计时"', main)
        self.assertIn('Layout.preferredHeight: 252', main)
        self.assertIn('Layout.preferredHeight: 150', main)

    def test_2_3_task_center_keeps_primary_controls_in_default_window(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        tasks_index = main.index("// Tasks page")
        smart_index = main.index("// Smart triggers page", tasks_index)
        tasks_section = main[tasks_index:smart_index]

        self.assertIn("ScrollView {", tasks_section)
        self.assertIn("id: taskCenterScroll", tasks_section)
        self.assertIn("contentWidth: availableWidth", tasks_section)
        self.assertIn('Layout.preferredHeight: 140', tasks_section)
        self.assertIn('Layout.preferredHeight: 116', tasks_section)
        self.assertIn('Task Queue Dashboard · 任务队列', tasks_section)
        self.assertIn('Recent activity · 最近日志', tasks_section)

    def test_2_3_task_center_uses_two_columns_to_avoid_below_fold_content(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        tasks_index = main.index("// Tasks page")
        smart_index = main.index("// Smart triggers page", tasks_index)
        tasks_section = main[tasks_index:smart_index]

        self.assertIn("id: taskCenterColumns", tasks_section)
        self.assertIn("id: taskTemplateColumn", tasks_section)
        self.assertIn("id: queueAndActivityColumn", tasks_section)
        self.assertIn("Layout.preferredWidth: 330", tasks_section)
        self.assertIn('Layout.preferredHeight: 156', tasks_section)
        self.assertIn('Layout.preferredHeight: 116', tasks_section)
        self.assertIn('Layout.preferredHeight: 140', tasks_section)

    def test_2_3_task_center_scrollview_closes_before_smart_triggers(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        tasks_index = main.index("// Tasks page")
        smart_index = main.index("// Smart triggers page", tasks_index)
        between = main[tasks_index:smart_index]

        self.assertIn("id: taskCenterScroll", between)
        self.assertIn("\n                }\n            }\n        }\n", between)

    def test_smart_trigger_page_scrolls_to_keep_controls_accessible(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        smart_index = main.index("// Smart triggers page")
        script_index = main.index("// Script page", smart_index)
        smart_section = main[smart_index:script_index]

        self.assertIn("ScrollView {", smart_section)
        self.assertIn("contentWidth: availableWidth", smart_section)
        self.assertIn("clip: true", smart_section)

    def test_dry_run_switch_requires_confirmation_before_live_mode(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        settings_index = main.index("// Settings page")
        live_dialog_index = main.index("id: liveModeConfirmDialog") if "id: liveModeConfirmDialog" in main else len(main)
        settings_section = main[settings_index:live_dialog_index]

        self.assertIn("id: liveModeConfirmDialog", main)
        self.assertIn("id: dryRunSafetySwitch", settings_section)
        self.assertIn("mainWindow.confirmLiveModeFromSwitch(checked)", settings_section)
        self.assertIn("liveModeConfirmDialog.open()", main)
        self.assertIn("mainWindow.syncDryRunSwitchState()\n        liveModeConfirmDialog.open()", main)
        self.assertIn("controller.requestDryRunChange(false)", main)
        self.assertIn("onRejected: mainWindow.syncDryRunSwitchState()", main)
        self.assertNotIn("controller.requestDryRunChange(checked)", settings_section)
        self.assertLess(main.index("liveModeConfirmDialog.open()"), main.index("controller.requestDryRunChange(false)"))

    def test_live_mode_warning_describes_scheduled_and_trigger_confirmation_limits(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertIn("立即执行按钮会再次弹窗", main)
        self.assertIn("倒计时和进程/网络触发到点后不会再次确认", main)
        self.assertNotIn("危险动作仍会弹窗确认", main)

    def test_full_polish_controls_are_wired(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        for snippet in (
            "mainWindow.confirmLiveModeFromSwitch(checked)",
            "controller.exportDiagnostics()",
            "controller.snoozeMinutes(5)",
            "controller.snoozeMinutes(10)",
            "applyTaskTemplate(\"lock_5\")",
            "applyTaskTemplate(\"sleep_10\")",
            "applyTaskTemplate(\"shutdown_midnight\")",
            "mainWindow.toggleMaximized()",
            "onDoubleClicked: mainWindow.toggleMaximized()",
        ):
            self.assertIn(snippet, main)

        for label in ("LIVE MODE 会执行真实系统动作", "导出诊断", "延后 5 分钟", "延后 10 分钟", "5 分钟后锁定", "10 分钟后睡眠", "明天 00:00 关机"):
            self.assertIn(label, main)


if __name__ == "__main__":
    unittest.main()
