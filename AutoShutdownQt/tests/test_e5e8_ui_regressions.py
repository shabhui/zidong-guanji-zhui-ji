from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
QML = ROOT / "AutoShutdownQt" / "qml"
APP_DIR = ROOT / "AutoShutdownQt"
MAIN_QML = QML / "Main.qml"
CONTROLLER_PY = APP_DIR / "controller.py"
CONFIRM_DIALOG_QML = QML / "components" / "ConfirmDialog.qml"
NEON_BUTTON_QML = QML / "components" / "NeonButton.qml"
ACTION_TILE_QML = QML / "components" / "ActionTile.qml"
TASK_QUEUE_DASHBOARD_QML = QML / "components" / "TaskQueueDashboard.qml"
RECENT_ACTIVITY_PANEL_QML = QML / "components" / "RecentActivityPanel.qml"
TASK_TEMPLATE_PANEL_QML = QML / "components" / "TaskTemplatePanel.qml"
TASK_MODEL_PY = APP_DIR / "task_model.py"
TASK_SCHEDULER_PY = APP_DIR / "task_scheduler.py"
STARRY_MASCOT_QML = QML / "components" / "StarryMascot.qml"
STATUS_HERO_QML = QML / "components" / "StatusHero.qml"
SIDEBAR_ITEM_QML = QML / "components" / "SidebarItem.qml"


def main_and_task_queue_qml():
    task_queue = TASK_QUEUE_DASHBOARD_QML.read_text(encoding="utf-8") if TASK_QUEUE_DASHBOARD_QML.exists() else ""
    recent_activity = RECENT_ACTIVITY_PANEL_QML.read_text(encoding="utf-8") if RECENT_ACTIVITY_PANEL_QML.exists() else ""
    task_template = TASK_TEMPLATE_PANEL_QML.read_text(encoding="utf-8") if TASK_TEMPLATE_PANEL_QML.exists() else ""
    return MAIN_QML.read_text(encoding="utf-8") + "\n" + task_queue + "\n" + recent_activity + "\n" + task_template


class E5E8ButtonRegressionTest(unittest.TestCase):
    def test_main_uses_neon_buttons_instead_of_default_fusion_buttons(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertTrue(NEON_BUTTON_QML.exists(), "NeonButton.qml should define the e5e8 glass button skin")
        self.assertNotRegex(main, r"(?m)^\s*Button\s*\{", "Main.qml should not use unskinned Qt Fusion Button controls")
        self.assertGreaterEqual(main.count("NeonButton {"), 11, "Main.qml should skin title, hero, preset, timer, and task buttons")

    def test_quick_countdown_presets_are_two_by_two_neon_chips(self):
        main = MAIN_QML.read_text(encoding="utf-8")
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

        self.assertIn("height: 300", main, "hero card should leave room for the immediate execute button")
        self.assertIn("height: 150", main, "quick countdown row should fit chips while leaving room for action tiles")
        self.assertIn("height: parent.height - y", power_section, "overview action card should fill the remaining left column without overlapping")
        self.assertIn("anchors.margins: 14", power_section, "overview action card needs compact margins")
        self.assertIn("rowSpacing: 6", power_section, "overview action grid needs compact row spacing")
        self.assertEqual(power_section.count("Layout.preferredHeight: 56"), 6, "overview action tiles need fixed compact heights")

    def test_core_mvp_pages_are_wired_to_controller(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        qml_source = main_and_task_queue_qml()
        main = qml_source

        for template_key in ("shutdown_15", "shutdown_30", "sleep_60", "shutdown_2300"):
            self.assertIn(f'applyTaskTemplate("{template_key}")', qml_source)
        for label in ("15 分钟后关机", "30 分钟后关机", "1 小时后睡眠", "今晚 23:00 关机"):
            self.assertIn(label, qml_source)

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
        qml_source = main_and_task_queue_qml()

        for snippet in (
            "定时关机助手 v3.2",
            "v3.2 · 清晰工作台",
            "controller.queueRowsJson",
            "JSON.parse(controller.queueRowsJson)",
            "controller.addFixedTimeTask(",
            "controller.setQueueTaskEnabled(",
            "controller.deleteQueueTask(",
            "controller.runQueueTaskDryRunCheck(",
            "repeatRuleCombo",
        ):
            self.assertIn(snippet, qml_source)
        for label in ("任务队列", "重复规则", "仅一次", "每天", "工作日", "周末", "安全检查", "删除"):
            self.assertIn(label, qml_source)

    def test_task_queue_list_model_refreshes_when_controller_queue_changes(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        task_queue = TASK_QUEUE_DASHBOARD_QML.read_text(encoding="utf-8")

        self.assertIn("property var queueRowModel", main)
        self.assertIn("queueRowModel: queueRows()", main)
        self.assertIn("function onTaskQueueChanged()", main)
        self.assertIn("mainWindow.queueRowModel = mainWindow.queueRows()", main)
        self.assertIn("queueRows: mainWindow.queueRowModel", main)
        self.assertIn("model: root.queueRows", task_queue)
        self.assertNotIn("model: mainWindow.queueRows()", main)

    def test_neon_card_hover_layer_does_not_steal_child_clicks(self):
        card = (QML / "components" / "NeonCard.qml").read_text(encoding="utf-8")

        self.assertNotIn("MouseArea {", card)
        self.assertIn("HoverHandler {", card)

    def test_neon_buttons_use_flat_state_layers_without_glow(self):
        button = NEON_BUTTON_QML.read_text(encoding="utf-8")

        self.assertNotIn("Theme.glowPink", button)
        self.assertNotIn("Theme.glowBlue", button)
        self.assertNotIn("opacity: root.enabled &&", button)
        self.assertIn("opacity: root.enabled ? 0.22 : 0.10", button)

    def test_2_2_tray_copy_mentions_availability_and_explicit_quit(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertIn("托盘可用时关闭窗口会隐藏到后台", main)
        self.assertIn("托盘不可用时关闭窗口不会继续后台运行", main)
        self.assertIn("托盘菜单“退出程序”", main)
        self.assertIn("if (controller.trayAvailable && !trayCloseRequested)", main)
        self.assertIn("controller.minimizeToTray()", main)

    def test_main_starts_music_autoplay_after_qml_loads(self):
        main_py = (ROOT / "AutoShutdownQt" / "main.py").read_text(encoding="utf-8")

        self.assertIn("from music_service import MusicService", main_py)
        self.assertIn("from notification_service import NotificationService", main_py)
        self.assertIn("from startup_service import StartupService", main_py)
        self.assertIn("else StartupService()", main_py)
        self.assertIn("startup_service=ScreenshotStartupService() if screenshot_path is not None else StartupService()", main_py)
        self.assertIn("controller.notificationService = NotificationService(tray_service=tray_service, logger=controller._add_log)", main_py)
        self.assertNotIn("if controller.startMinimizedToTray and tray_service.available:", main_py)
        self.assertNotIn("window.hide()", main_py)
        self.assertIn("controller.startMusicAutoplay()", main_py)
        self.assertGreater(main_py.index("engine.load(str(main_qml))"), main_py.index("engine.rootContext().setContextProperty"))
        self.assertGreater(main_py.index("controller.startMusicAutoplay()"), main_py.index("if not engine.rootObjects():"))

    def test_main_sets_application_and_window_icon_from_packaged_image(self):
        main_py = (ROOT / "AutoShutdownQt" / "main.py").read_text(encoding="utf-8")
        main = MAIN_QML.read_text(encoding="utf-8")
        title_section = main[main.index("id: titleBar"):main.index("// Sidebar")]

        self.assertIn("from PySide6.QtGui import QIcon", main_py)
        self.assertIn('APP_ICON_PATH = Path(__file__).parent / "app_icon.png"', main_py)
        self.assertIn("app.setWindowIcon(QIcon(str(APP_ICON_PATH)))", main_py)
        self.assertIn("window.setIcon(QIcon(str(APP_ICON_PATH)))", main_py)
        self.assertIn("TrayService(controller, window, icon_path=APP_ICON_PATH", main_py)
        self.assertIn("Image {", title_section)
        self.assertIn('source: "../app_icon.png"', title_section)
        self.assertNotIn('text: "AS"', title_section)
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

    def test_3_2_first_run_safety_guide_is_wired(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertIn("id: firstRunSafetyGuideDialog", main)
        self.assertIn("controller.firstRunSafetyGuideShown", main)
        self.assertIn("controller.acknowledgeFirstRunSafetyGuide()", main)
        self.assertIn("安全验证模式默认开启", main)
        self.assertIn("关闭安全验证后可能真实执行", main)
        self.assertIn("右下角托盘", main)
        self.assertIn("彻底退出", main)

    def test_3_2_close_to_tray_hint_is_wired(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertIn("id: trayCloseHintDialog", main)
        self.assertIn("controller.trayCloseHintShown", main)
        self.assertIn("controller.acknowledgeTrayCloseHint()", main)
        self.assertIn("trayCloseHintDialog.open()", main)
        self.assertIn("任务、倒计时和触发器仍会继续", main)
        self.assertIn("controller.minimizeToTray()", main)

    def test_3_2_live_mode_warning_copy_is_stronger(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        dialog = CONFIRM_DIALOG_QML.read_text(encoding="utf-8")

        self.assertIn("真实执行模式：请确认未保存工作", main)
        self.assertIn("真实执行模式会真实执行当前动作", dialog)
        self.assertIn("可能导致关机、重启、睡眠、休眠、注销或锁定", dialog)
        self.assertIn("controller.dryRun ?", dialog)

    def test_2_5_main_wires_notifications_startup_and_start_minimized(self):
        main_py = (ROOT / "AutoShutdownQt" / "main.py").read_text(encoding="utf-8")

        self.assertIn('app.setApplicationVersion("3.2")', main_py)
        self.assertIn("from notification_service import NotificationService", main_py)
        self.assertIn("from startup_service import StartupService", main_py)
        self.assertIn("controller.notificationService = NotificationService(tray_service=tray_service", main_py)
        self.assertIn("else StartupService()", main_py)
        self.assertIn("startup_service=ScreenshotStartupService() if screenshot_path is not None else StartupService()", main_py)
        self.assertNotIn("if controller.startMinimizedToTray and tray_service.available:", main_py)
        self.assertNotIn("window.hide()", main_py)

    def test_music_player_ui_is_wired_to_controller(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        for snippet in (
            "id: musicPlayerWindow",
            'objectName: "musicPlayerWindow"',
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
            'title: "定时关机助手 v3.2"',
            'id: rightStatusPanel',
            '安全模式',
            '安全验证已开启',
            '下一任务',
            '队列数量',
            '触发器状态',
            '后台托盘',
            '最近活动',
        ):
            self.assertIn(snippet, main)

        self.assertNotIn('定时关机助手 v3.2 · Command Center', main)
        self.assertNotIn('Text { text: "Command Center"', main)
        self.assertNotIn('Text { text: "Next task"', main)
        self.assertNotIn('Text { text: "Active triggers"', main)
        self.assertNotIn('Text { text: "Queue health"', main)
        self.assertNotIn('v3.2 · 右侧状态栏', main)

    def test_market_polish_keeps_primary_chrome_fully_localized(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        qml_source = main_and_task_queue_qml()
        title_section = main[main.index("id: titleBar"):main.index("// Sidebar")]

        self.assertIn('text: "定时关机助手"', title_section)
        self.assertNotIn('text: "AutoShutdown"', title_section)

        for stale_label in ("RUNNING", "PAUSED", "READY", "NAVIGATION", "SHUTDOWN", "SLEEP", "HIBERNATE", "RESTART", "LOG OUT", "LOCK"):
            self.assertNotIn(stale_label, qml_source)

        for stale_stage_copy in ("Ready |", "Script preflight", "Current:", "Skip available", "Skip unavailable"):
            self.assertNotIn(stale_stage_copy, qml_source)

        for localized_label in ("运行中", "已暂停", "就绪", "导航", "模拟关机", "进入睡眠", "进入休眠", "重新启动", "退出登录", "锁定屏幕"):
            self.assertIn(localized_label, qml_source)

        for tooltip in ("打开音乐播放器", "最小化", "最大化/还原", "关闭到托盘或退出"):
            self.assertIn(f'ToolTip.text: "{tooltip}"', title_section)

    def test_unused_starry_mascot_component_is_removed(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertFalse(STARRY_MASCOT_QML.exists())
        self.assertNotIn("StarryMascot", main)

    def test_unused_legacy_shell_components_are_removed_from_release_qml(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        for component_path in (STATUS_HERO_QML, SIDEBAR_ITEM_QML):
            with self.subTest(component=component_path.name):
                self.assertFalse(component_path.exists())

        for component_name in ("StatusHero", "SidebarItem"):
            self.assertNotIn(component_name, main)

    def test_visible_safety_mode_and_exit_copy_uses_product_chinese(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        dialog = CONFIRM_DIALOG_QML.read_text(encoding="utf-8")
        visible_qml = main + "\n" + dialog

        for stale_copy in ('"DRY RUN"', '"LIVE MODE"', "进入 LIVE MODE", "托盘菜单 Quit", "选择 Quit"):
            self.assertNotIn(stale_copy, visible_qml)

        for label in ("安全验证", "真实执行模式", "关闭安全验证", "进入真实执行模式", "托盘菜单“退出程序”"):
            self.assertIn(label, visible_qml)
        self.assertIn("安全验证模式只记录当前动作", dialog)

    def test_visible_safety_help_copy_does_not_expose_dry_run_jargon(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertNotIn("Dry-run", main)
        for label in (
            "安全验证开启时只验证流程",
            "安全验证会只记录模拟执行",
            "安全验证下只记录模拟执行",
            "继续复用安全验证、提醒、历史和取消逻辑",
            "安全验证下只记录将执行的脚本",
            "安全验证模式",
        ):
            self.assertIn(label, main)

    def test_task_queue_rows_render_localized_status_label(self):
        task_queue = TASK_QUEUE_DASHBOARD_QML.read_text(encoding="utf-8")

        self.assertIn('modelData.statusLabel + " · " + modelData.nextRunText', task_queue)
        self.assertNotIn('modelData.status + " · " + modelData.nextRunText', task_queue)

    def test_task_repeat_validation_copy_is_not_tied_to_old_version(self):
        task_model = TASK_MODEL_PY.read_text(encoding="utf-8")
        task_scheduler = TASK_SCHEDULER_PY.read_text(encoding="utf-8")
        combined = task_model + "\n" + task_scheduler

        self.assertNotIn("AutoShutdownQt 2.1", combined)
        self.assertIn('"only fixed_time tasks can repeat"', task_model)
        self.assertIn('("only fixed_time tasks can repeat", "仅固定时间任务支持重复")', task_scheduler)

    def test_2_3_status_panel_does_not_push_overview_below_fold(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertIn('id: rightStatusPanel', main)
        self.assertNotIn("id: safetyStrip", main)
        self.assertNotIn("id: commandCardsRow", main)
        self.assertNotIn("id: commandCenterScroll", main)
        self.assertIn('Text { text: "快捷倒计时"', main)
        self.assertIn('height: 300', main)
        self.assertIn('height: 150', main)

    def test_overview_is_reworked_as_a_clear_workbench(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        overview_index = main.index("// Overview page")
        timer_index = main.index("// Timer page", overview_index)
        overview_section = main[overview_index:timer_index]

        for snippet in (
            "id: overviewWorkbench",
            "id: currentTaskPanel",
            "id: overviewActionPanel",
            "id: quickCountdownPanel",
            "id: overviewStatusSummary",
            "id: overviewRecentActivity",
        ):
            self.assertIn(snippet, overview_section)

        self.assertIn("readonly property int overviewRightWidth: 360", overview_section)
        self.assertNotIn("v3.2 路 鍙充晶鐘舵€佹爮", overview_section)
        self.assertNotIn("font.letterSpacing", overview_section)

    def test_overview_uses_explicit_geometry_to_prevent_panel_overlap(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        overview_index = main.index("// Overview page")
        timer_index = main.index("// Timer page", overview_index)
        overview_section = main[overview_index:timer_index]

        self.assertIn("readonly property int overviewGap", overview_section)
        self.assertIn("readonly property int overviewRightWidth", overview_section)
        self.assertIn("readonly property int overviewLeftWidth", overview_section)
        self.assertIn("width: overviewWorkbench.overviewLeftWidth", overview_section)
        self.assertIn("x: overviewWorkbench.overviewLeftWidth + overviewWorkbench.overviewGap", overview_section)
        self.assertIn("width: overviewWorkbench.overviewRightWidth", overview_section)
        self.assertIn("y: quickCountdownPanel.height + overviewWorkbench.overviewGap", overview_section)
        self.assertIn("height: parent.height - y", overview_section)
        self.assertNotIn("RowLayout {\n                id: overviewWorkbench", overview_section)

    def test_overview_cards_use_opaque_panels_to_prevent_text_bleed_through(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        overview_index = main.index("// Overview page")
        timer_index = main.index("// Timer page", overview_index)
        overview_section = main[overview_index:timer_index]

        self.assertGreaterEqual(overview_section.count("cardColor: Theme.dialogPanel"), 4)
        self.assertIn("cardColor: Theme.dialogPanelRaised", overview_section)
        self.assertNotIn("cardColor: Theme.cardGlass", overview_section)
        self.assertNotIn("active: true", overview_section)
        self.assertNotIn("breathing: true", overview_section)

    def test_current_task_panel_stacks_content_in_narrow_overview_column(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        panel_index = main.index("id: currentTaskPanel")
        action_index = main.index("id: overviewActionPanel", panel_index)
        panel_section = main[panel_index:action_index]

        self.assertIn("id: currentTaskContent", panel_section)
        self.assertIn("id: currentTaskActions", panel_section)
        self.assertIn("GridLayout {", panel_section)
        self.assertIn("columns: 2", panel_section)
        self.assertNotIn("Layout.preferredWidth: 230", panel_section)
        self.assertNotIn("font.pixelSize: 70", panel_section)

    def test_shell_navigation_and_title_bar_use_solid_readable_surfaces(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        shell_section = main[main.index("id: appShell"):main.index("// Title bar")]
        title_section = main[main.index("id: titleBar"):main.index("// Sidebar")]
        nav_section = main[main.index("id: navigationRail"):main.index("Item {\n        id: contentHost")]

        self.assertIn("cardColor: Theme.dialogPanel", shell_section)
        self.assertIn("color: Theme.dialogPanel", title_section)
        self.assertIn("cardColor: Theme.dialogPanel", nav_section)
        self.assertIn("color: Theme.dialogPanelRaised", nav_section)
        self.assertNotIn("cardColor: Theme.shellGlass", shell_section)
        self.assertNotIn("color: Theme.glassSoft", title_section)
        self.assertNotIn("font.letterSpacing", nav_section)

    def test_main_pages_use_solid_readable_surfaces_after_overview(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        page_ranges = [
            ("// Timer page", "// Tasks page"),
            ("// Tasks page", "// Smart triggers page"),
            ("// Smart triggers page", "// Script page"),
            ("// Script page", "// Settings page"),
            ("// Settings page", "Window {"),
        ]

        for start_marker, end_marker in page_ranges:
            with self.subTest(page=start_marker):
                start = main.index(start_marker)
                end = main.index(end_marker, start)
                section = main[start:end]
                card_start = section.index("NeonCard {")
                card_end_candidates = [
                    index
                    for index in (
                        section.find("\n                NeonCard {", card_start + 1),
                        section.find("ScrollView {", card_start),
                        section.find("ColumnLayout {", card_start),
                    )
                    if index != -1 and index > card_start
                ]
                first_card = section[card_start:min(card_end_candidates) if card_end_candidates else len(section)]

                self.assertRegex(first_card, r"cardColor: Theme\.dialogPanel(Raised)?")
                self.assertNotIn("cardColor: Theme.cardGlass", first_card)
                self.assertNotIn("cardColor: Theme.cardGlassActive", first_card)

    def test_dense_action_rows_can_wrap_instead_of_overflowing(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        task_template = TASK_TEMPLATE_PANEL_QML.read_text(encoding="utf-8")

        tasks_index = main.index("// Tasks page")
        smart_index = main.index("// Smart triggers page", tasks_index)
        script_index = main.index("// Script page", smart_index)
        settings_index = main.index("// Settings page", script_index)

        tasks_section = main[tasks_index:smart_index]
        smart_section = main[smart_index:script_index]
        script_section = main[script_index:settings_index]
        settings_section = main[settings_index:main.index("Window {", settings_index)]

        self.assertIn("TaskTemplatePanel {", tasks_section)
        self.assertIn("id: taskPrimaryActions", task_template)
        task_actions_index = task_template.index("id: taskPrimaryActions")
        self.assertIn("Flow {", task_template[task_template.rfind("Flow {", 0, task_actions_index):task_actions_index])
        self.assertIn("id: processTriggerActions", smart_section)
        self.assertIn("id: networkTriggerActions", smart_section)
        self.assertIn("id: idleTriggerActions", smart_section)
        self.assertIn("id: scriptActionFlow", script_section)
        self.assertIn("id: historyActionFlow", settings_section)

    def test_script_log_panel_has_status_strip_and_bounded_viewport(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        smart_index = main.index("// Smart triggers page")
        script_index = main.index("// Script page", smart_index)
        settings_index = main.index("// Settings page", script_index)
        script_section = main[script_index:settings_index]

        self.assertIn("id: scriptLogPanel", script_section)
        self.assertIn("id: scriptLogStatusStrip", script_section)
        self.assertIn("id: scriptLogViewport", script_section)
        self.assertIn('controller.scriptEnabled ? "已启用" : "未启用"', script_section)
        self.assertIn('controller.scriptPath ? "路径已填写" : "路径未填写"', script_section)
        self.assertIn('"超时 " + controller.scriptTimeoutSeconds + " 秒"', script_section)

    def test_smart_trigger_forms_are_not_hard_packed_into_wide_grids(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        smart_index = main.index("// Smart triggers page")
        script_index = main.index("// Script page", smart_index)
        smart_section = main[smart_index:script_index]

        self.assertIn("id: networkThresholdGrid", smart_section)
        self.assertIn("id: idleTriggerGrid", smart_section)
        network_grid = smart_section[smart_section.index("id: networkThresholdGrid"):smart_section.index("id: networkTriggerActions")]
        self.assertIn("columns: 4", network_grid)
        self.assertIn("columns: 2", smart_section[smart_section.index("id: idleTriggerGrid"):])
        self.assertNotIn("columns: 6", smart_section)

    def test_settings_page_is_grouped_into_scannable_panels(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        settings_index = main.index("// Settings page")
        settings_section = main[settings_index:main.index("Window {", settings_index)]

        self.assertIn("id: settingsPanelGrid", settings_section)
        settings_grid = settings_section[settings_section.index("id: settingsPanelGrid"):]
        self.assertIn("columns: 2", settings_grid)

        for panel_id in (
            "id: settingsSafetyPanel",
            "id: settingsReminderPanel",
            "id: settingsSystemPanel",
        ):
            self.assertIn(panel_id, settings_section)

        self.assertGreaterEqual(settings_section.count("cardColor: Theme.dialogPanelRaised"), 3)
        self.assertIn("id: settingsLiveModeWarning", settings_section)
        self.assertIn("Layout.column: 0", settings_section[settings_section.index("id: settingsLiveModeWarning"):])
        self.assertIn("Layout.column: 1", settings_section[settings_section.index("id: settingsReminderPanel"):])
        self.assertIn("Layout.column: 1", settings_section[settings_section.index("id: settingsSystemPanel"):])

    def test_settings_panels_leave_room_for_help_text_and_style_inputs(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        settings_index = main.index("// Settings page")
        settings_section = main[settings_index:main.index("Window {", settings_index)]

        self.assertIn("Layout.preferredHeight: 286", settings_section)
        self.assertIn("Layout.preferredHeight: 206", settings_section)
        self.assertIn("Layout.preferredHeight: 190", settings_section)
        self.assertIn("Layout.preferredWidth: (settingsPanelGrid.width - settingsPanelGrid.columnSpacing) / 2", settings_section)
        self.assertIn("Layout.preferredWidth: 210", settings_section)
        self.assertIn("width: 78", settings_section)
        self.assertEqual(settings_section.count("background: Rectangle { color: Theme.inputGlass"), 4)
        self.assertNotIn("Layout.preferredHeight: 94", settings_section)
        self.assertNotIn("Layout.preferredHeight: 214", settings_section)
        self.assertNotIn("Layout.preferredWidth: 420", settings_section)
        self.assertNotIn("Layout.preferredHeight: 250", settings_section)

    def test_settings_live_mode_warning_is_framed_as_a_safety_panel(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        settings_index = main.index("// Settings page")
        settings_section = main[settings_index:main.index("Window {", settings_index)]

        self.assertIn("NeonCard {\n                                id: settingsLiveModeWarning", settings_section)
        self.assertIn("cardBorderColor: Theme.danger", settings_section)
        self.assertIn('Text { text: "真实执行提醒"', settings_section)
        self.assertIn("maximumLineCount: 3", settings_section)
        self.assertNotIn("Text {\n                                id: settingsLiveModeWarning", settings_section)

    def test_timer_page_exposes_action_context_before_scheduling(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        timer_index = main.index("// Timer page")
        tasks_index = main.index("// Tasks page", timer_index)
        timer_section = main[timer_index:tasks_index]

        self.assertIn("id: timerActionContextCard", timer_section)
        self.assertIn("id: timerActionCombo", timer_section)
        self.assertIn("controller.actionLabel", timer_section)
        self.assertIn("function syncFromController()", timer_section)
        self.assertIn("if (!syncing) controller.selectedAction = currentValue", timer_section)
        self.assertLess(timer_section.index("id: timerActionContextCard"), timer_section.index("controller.startCountdown("))
        for action in ("shutdown", "sleep", "hibernate", "restart", "logoff", "lock"):
            self.assertIn(f'value: "{action}"', timer_section)

    def test_smart_trigger_cards_are_compact_enough_to_reveal_idle_section(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        smart_index = main.index("// Smart triggers page")
        script_index = main.index("// Script page", smart_index)
        smart_section = main[smart_index:script_index]

        self.assertIn("id: smartTriggerTopGrid", smart_section)
        self.assertIn("columns: 2", smart_section[smart_section.index("id: smartTriggerTopGrid"):])
        self.assertIn("Layout.preferredHeight: 206", smart_section)
        self.assertIn("Layout.preferredHeight: 242", smart_section)
        self.assertIn("id: idleTriggerPreviewSpacer", smart_section)
        self.assertIn("id: idleTriggerControlRow", smart_section)
        self.assertLess(smart_section.index("id: idleTriggerPreviewSpacer"), smart_section.index('text: "触发日志"'))
        self.assertLess(smart_section.index("id: idleTriggerGrid"), smart_section.index("id: idleTriggerActions"))
        self.assertNotIn("Layout.preferredHeight: 236", smart_section)

    def test_music_player_window_uses_solid_panel_surface(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        music_index = main.index("id: musicPlayerWindow")
        music_section = main[music_index:main.index("id: firstRunSafetyGuideDialog", music_index)]

        self.assertIn("cardColor: Theme.dialogPanelRaised", music_section)
        self.assertNotIn("cardColor: Theme.cardGlassActive", music_section)

    def test_music_player_window_leaves_room_for_volume_controls(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        music_index = main.index("id: musicPlayerWindow")
        music_section = main[music_index:main.index("id: firstRunSafetyGuideDialog", music_index)]

        self.assertIn("height: 560", music_section)
        self.assertIn("minimumHeight: 520", music_section)
        self.assertNotIn("height: 520", music_section)

    def test_music_player_empty_playlist_has_framed_empty_state(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        music_index = main.index("id: musicPlayerWindow")
        music_section = main[music_index:main.index("id: firstRunSafetyGuideDialog", music_index)]

        self.assertIn("id: musicPlaylistFrame", music_section)
        self.assertIn("id: musicEmptyPlaylistState", music_section)
        self.assertIn("visible: mainWindow.musicTrackModel.length === 0", music_section)
        self.assertIn("anchors.centerIn: parent", music_section)

    def test_main_py_can_capture_qt_ui_screenshot_for_visual_regression(self):
        main_py = (APP_DIR / "main.py").read_text(encoding="utf-8")

        self.assertIn("--ui-screenshot", main_py)
        self.assertIn("--ui-page", main_py)
        self.assertIn("--ui-target", main_py)
        self.assertIn("def _parse_screenshot_target(argv):", main_py)
        self.assertIn("def _screenshot_capture_window(window, screenshot_target):", main_py)
        self.assertIn("QTimer.singleShot", main_py)
        self.assertIn('window.findChild(QObject, "musicPlayerWindow")', main_py)
        self.assertIn("capture_window.grabWindow()", main_py)
        self.assertIn("screenshot_path", main_py)
        self.assertIn("if screenshot_path is None:", main_py)
        self.assertIn("window.setProperty(\"currentPage\", screenshot_page)", main_py)
        self.assertIn("controller._dry_run = True", main_py)
        self.assertIn("controller._first_run_safety_guide_shown = True", main_py)
        self.assertIn("tray_service.setup()", main_py)
        self.assertIn("controller.startMusicAutoplay()", main_py)

    def test_ui_screenshot_mode_uses_null_settings_path_for_clean_visuals(self):
        main_py = (APP_DIR / "main.py").read_text(encoding="utf-8")

        self.assertIn("import os", main_py)
        self.assertIn("def _screenshot_settings_path(screenshot_path):", main_py)
        self.assertIn("return Path(os.devnull) if screenshot_path is not None else None", main_py)
        self.assertIn("settings_path=_screenshot_settings_path(screenshot_path)", main_py)

    def test_ui_screenshot_mode_accepts_window_size_for_responsive_checks(self):
        main_py = (APP_DIR / "main.py").read_text(encoding="utf-8")

        self.assertIn("--ui-width", main_py)
        self.assertIn("--ui-height", main_py)
        self.assertIn("def _parse_screenshot_size(argv):", main_py)
        self.assertIn("screenshot_width, screenshot_height = _parse_screenshot_size(sys.argv)", main_py)
        self.assertIn("window.setWidth(screenshot_width)", main_py)
        self.assertIn("window.setHeight(screenshot_height)", main_py)

    def test_neon_cards_use_restrained_decoration_on_solid_panels(self):
        neon_card = (QML / "components" / "NeonCard.qml").read_text(encoding="utf-8")

        self.assertIn("opacity: 0.18", neon_card)
        self.assertNotIn("opacity: 0.28", neon_card)
        self.assertNotIn("radius: width / 2", neon_card)
        self.assertNotIn("Theme.e5Blue", neon_card)
        self.assertNotIn("Theme.e5Pink", neon_card)
        self.assertNotIn("property bool breathing", neon_card)
        self.assertNotIn("SequentialAnimation on opacity", neon_card)
        self.assertNotIn("opacity: 0.78", neon_card)
        self.assertNotIn("? 0.18 : 0.09", neon_card)

    def test_2_3_task_center_keeps_primary_controls_in_default_window(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        task_template = TASK_TEMPLATE_PANEL_QML.read_text(encoding="utf-8")
        task_queue = TASK_QUEUE_DASHBOARD_QML.read_text(encoding="utf-8")
        recent_activity = RECENT_ACTIVITY_PANEL_QML.read_text(encoding="utf-8")
        tasks_index = main.index("// Tasks page")
        smart_index = main.index("// Smart triggers page", tasks_index)
        tasks_section = main[tasks_index:smart_index]

        self.assertIn("ScrollView {", tasks_section)
        self.assertIn("id: taskCenterScroll", tasks_section)
        self.assertIn("contentWidth: availableWidth", tasks_section)
        self.assertIn('TaskQueueDashboard {', tasks_section)
        self.assertIn('Layout.preferredHeight: 140', task_queue)
        self.assertIn('TaskTemplatePanel {', tasks_section)
        self.assertIn('Layout.preferredHeight: 116', task_template)
        self.assertIn('Task Queue Dashboard · 任务队列', task_queue)
        self.assertIn('RecentActivityPanel {', tasks_section)
        self.assertIn('Recent activity · 最近日志', recent_activity)
        self.assertIn('controller.logSummaryText', recent_activity)

    def test_task_queue_dashboard_uses_bounded_empty_viewport(self):
        task_queue = TASK_QUEUE_DASHBOARD_QML.read_text(encoding="utf-8")

        self.assertIn("id: taskQueueViewport", task_queue)
        self.assertIn("id: taskQueueEmptyState", task_queue)
        self.assertIn("visible: root.queueRows.length === 0", task_queue)
        self.assertIn("anchors.centerIn: parent", task_queue)
        self.assertIn("anchors.margins: 8", task_queue)

    def test_task_queue_empty_state_reads_as_a_subtle_status_panel(self):
        task_queue = TASK_QUEUE_DASHBOARD_QML.read_text(encoding="utf-8")
        empty_index = task_queue.index("id: taskQueueEmptyState")
        empty_section = task_queue[task_queue.rfind("ColumnLayout {", 0, empty_index):]

        self.assertIn("color: Theme.dialogPanelRaised", task_queue)
        self.assertIn("ColumnLayout {", empty_section)
        self.assertIn('text: "队列为空"', empty_section)
        self.assertIn('text: "当前没有等待执行的任务"', empty_section)
        self.assertIn("horizontalAlignment: Text.AlignHCenter", empty_section)
        self.assertNotIn('text: "暂无排队任务"', empty_section)

    def test_2_3_task_center_uses_two_columns_to_avoid_below_fold_content(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        task_queue = TASK_QUEUE_DASHBOARD_QML.read_text(encoding="utf-8")
        task_template = TASK_TEMPLATE_PANEL_QML.read_text(encoding="utf-8")
        tasks_index = main.index("// Tasks page")
        smart_index = main.index("// Smart triggers page", tasks_index)
        tasks_section = main[tasks_index:smart_index]

        self.assertIn("id: taskCenterColumns", tasks_section)
        self.assertIn("id: taskTemplateColumn", tasks_section)
        self.assertIn("id: queueAndActivityColumn", tasks_section)
        self.assertIn("Layout.preferredWidth: 486", tasks_section)
        self.assertIn('Layout.preferredHeight: 156', task_template)
        self.assertIn('Layout.preferredHeight: 116', task_template)
        self.assertIn('Layout.preferredHeight: 140', task_queue)

    def test_2_3_task_center_columns_subtract_scroll_padding_to_keep_right_edge_visible(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        tasks_index = main.index("// Tasks page")
        smart_index = main.index("// Smart triggers page", tasks_index)
        tasks_section = main[tasks_index:smart_index]

        self.assertIn(
            "width: taskCenterScroll.availableWidth - taskCenterScroll.leftPadding - taskCenterScroll.rightPadding",
            tasks_section,
        )
        self.assertNotIn("width: taskCenterScroll.availableWidth\n", tasks_section)

    def test_2_3_task_center_column_widths_fit_minimum_window(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        tasks_index = main.index("// Tasks page")
        smart_index = main.index("// Smart triggers page", tasks_index)
        tasks_section = main[tasks_index:smart_index]

        self.assertIn("Layout.preferredWidth: 486", tasks_section)
        self.assertIn("Layout.minimumWidth: 438", tasks_section)
        self.assertIn("Layout.maximumWidth: 560", tasks_section)
        self.assertIn("Layout.preferredWidth: 292", tasks_section)
        self.assertIn("Layout.minimumWidth: 260", tasks_section)
        self.assertIn("Layout.maximumWidth: 310", tasks_section)
        self.assertNotIn("Layout.minimumWidth: 520", tasks_section)
        self.assertNotIn("Layout.minimumWidth: 360", tasks_section)

    def test_2_3_task_center_right_cards_leave_room_for_visible_borders(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        tasks_index = main.index("// Tasks page")
        smart_index = main.index("// Smart triggers page", tasks_index)
        tasks_section = main[tasks_index:smart_index]

        task_queue_usage = tasks_section[tasks_section.index("TaskQueueDashboard {"):tasks_section.index("RecentActivityPanel {")]
        recent_usage = tasks_section[tasks_section.index("RecentActivityPanel {"):tasks_section.index("}", tasks_section.index("RecentActivityPanel {"))]

        self.assertIn("Layout.rightMargin: 1", task_queue_usage)
        self.assertIn("Layout.rightMargin: 1", recent_usage)

    def test_2_3_task_center_right_column_has_stable_readable_width(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        tasks_index = main.index("// Tasks page")
        smart_index = main.index("// Smart triggers page", tasks_index)
        tasks_section = main[tasks_index:smart_index]

        self.assertIn("id: queueAndActivityColumn", tasks_section)
        self.assertIn("Layout.preferredWidth: 292", tasks_section)
        self.assertIn("Layout.minimumWidth: 260", tasks_section)
        self.assertIn("Layout.maximumWidth: 310", tasks_section)
        self.assertIn("Layout.fillWidth: false", tasks_section)
        self.assertIn("Layout.maximumWidth: 560", tasks_section)

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

    def test_smart_trigger_page_exposes_idle_shutdown_controls(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        smart_index = main.index("// Smart triggers page")
        script_index = main.index("// Script page", smart_index)
        smart_section = main[smart_index:script_index]

        for snippet in (
            "controller.idleTriggerEnabled",
            "controller.idleMinutes",
            "controller.idlePollSeconds",
            "controller.idleAction",
            "controller.startIdleTrigger()",
            "controller.stopIdleTrigger()",
            "controller.idleTriggerStatus",
        ):
            self.assertIn(snippet, smart_section)

        for label in ("空闲自动关机", "空闲分钟", "轮询秒", "开始空闲检测", "停止空闲检测"):
            self.assertIn(label, smart_section)

    def test_idle_action_combo_does_not_overwrite_saved_action_during_initial_sync(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        combo_index = main.index("id: idleActionCombo")
        combo_section = main[combo_index:main.index("NeonButton { width: 142", combo_index)]

        self.assertIn("property bool syncing: true", combo_section)
        self.assertIn("if (!syncing) controller.idleAction = currentValue", combo_section)
        self.assertIn("syncing = false", combo_section)

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

    def test_immediate_execute_buttons_disable_during_power_action(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertGreaterEqual(main.count("enabled: !controller.powerActionInProgress"), 2)

    def test_action_and_safety_controls_disable_during_power_action(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        action_tile = ACTION_TILE_QML.read_text(encoding="utf-8")

        self.assertIn("enabled: !controller.powerActionInProgress", action_tile)
        self.assertIn("mouseArea.enabled ? Qt.PointingHandCursor : Qt.ForbiddenCursor", action_tile)
        self.assertIn("id: dryRunSafetySwitch", main)
        self.assertIn("enabled: !controller.powerActionInProgress", main[main.index("id: dryRunSafetySwitch"):])
        self.assertRegex(main, r"FluentSwitch\s*\{\s*enabled: !controller\.powerActionInProgress\s*checked: controller\.forceClose")

    def test_power_action_progress_text_is_visible_near_immediate_execute(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        qml_source = main_and_task_queue_qml()

        self.assertGreaterEqual(qml_source.count("controller.powerActionProgressText"), 2)
        self.assertGreaterEqual(qml_source.count("controller.powerActionStepSummaryText"), 2)
        self.assertIn("visible: controller.powerActionInProgress", qml_source)

    def test_power_action_step_summary_is_localized_for_users(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        controller = CONTROLLER_PY.read_text(encoding="utf-8")

        self.assertIn("function formatPowerActionStepSummary(summary)", main)
        self.assertGreaterEqual(
            main.count("mainWindow.formatPowerActionStepSummary(controller.powerActionStepSummaryText)"),
            2,
        )
        self.assertIn("执行阶段：就绪", main)
        self.assertIn("脚本预检：等待", main)
        self.assertIn("关闭应用：等待", main)
        self.assertIn("系统动作：等待", main)
        self.assertIn("可跳过等待", controller)

    def test_skip_close_apps_wait_button_is_wired(self):
        qml_source = main_and_task_queue_qml()
        main = qml_source

        self.assertIn("跳过等待", main)
        self.assertIn("controller.skipCloseAppsWait()", qml_source)
        self.assertIn("controller.canSkipCloseAppsWait", qml_source)

    def test_close_apps_timeout_input_has_visible_range_guard(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        timeout_index = main.index("controller.closeAppsTimeoutSeconds")
        timeout_section = main[main.rfind("TextField {", 0, timeout_index):main.index("onEditingFinished", timeout_index)]
        self.assertIn("IntValidator", timeout_section)
        self.assertIn("bottom: 1", timeout_section)
        self.assertIn("top: 300", timeout_section)
        self.assertIn("1-300 秒", main)

    def test_close_apps_preview_button_is_wired(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertIn("预检关闭应用", main)
        self.assertIn("controller.previewCloseApps()", main)
        self.assertIn("enabled: !controller.powerActionInProgress", main)
        self.assertIn("controller.closeAppsPreviewText", main)
        self.assertIn("controller.closeAppsLastResultText", main)

    def test_diagnostics_center_and_failed_queue_recovery_are_wired(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        task_queue = TASK_QUEUE_DASHBOARD_QML.read_text(encoding="utf-8") if TASK_QUEUE_DASHBOARD_QML.exists() else ""
        qml_source = main + "\n" + task_queue

        for snippet in (
            "controller.copyDiagnostics()",
            "controller.diagnosticText",
            "controller.copyStatusText",
            "controller.runHealthCheck()",
            "controller.healthCheckText",
            "controller.setLogFilter(\"all\")",
            "controller.setLogFilter(\"warning\")",
            "controller.setLogFilter(\"error\")",
            "controller.filteredLogText",
            "controller.safetySummaryText",
            "controller.triggerHealthSummaryText",
            "controller.logCategorySummaryText",
            "controller.copyQueueTaskDiagnostic(modelData.id)",
            "controller.retryQueueTask(modelData.id)",
            "modelData.status === \"failed\"",
            "modelData.lastError",
        ):
            self.assertIn(snippet, qml_source)

    def test_task_queue_dashboard_is_extracted_from_main(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        self.assertTrue(TASK_QUEUE_DASHBOARD_QML.exists())
        self.assertIn("TaskQueueDashboard {", main)

    def test_recent_activity_panel_is_extracted_from_main(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        self.assertTrue(RECENT_ACTIVITY_PANEL_QML.exists())
        self.assertIn("RecentActivityPanel {", main)

    def test_task_template_panel_is_extracted_from_main(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        self.assertTrue(TASK_TEMPLATE_PANEL_QML.exists())
        self.assertIn("TaskTemplatePanel {", main)

    def test_task_center_copy_describes_workflow_instead_of_layout(self):
        task_template = TASK_TEMPLATE_PANEL_QML.read_text(encoding="utf-8")

        self.assertNotIn("左侧", task_template)
        self.assertNotIn("右侧", task_template)
        self.assertIn("选择模板创建队列任务，也可以立即执行当前动作。", task_template)
        self.assertIn('Text { text: "电源动作"', task_template)

    def test_full_polish_controls_are_wired(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        qml_source = main_and_task_queue_qml()

        for snippet in (
            "mainWindow.confirmLiveModeFromSwitch(checked)",
            "controller.exportDiagnostics()",
            "controller.queueSummaryText",
            "controller.snoozeMinutes(5)",
            "controller.snoozeMinutes(10)",
            "applyTaskTemplate(\"lock_5\")",
            "applyTaskTemplate(\"sleep_10\")",
            "applyTaskTemplate(\"shutdown_midnight\")",
            "mainWindow.toggleMaximized()",
            "onDoubleClicked: mainWindow.toggleMaximized()",
        ):
            self.assertIn(snippet, qml_source)

        for label in ("真实执行模式会执行真实系统动作", "导出诊断", "延后 5 分钟", "延后 10 分钟", "5 分钟后锁定", "10 分钟后睡眠", "明天 00:00 关机"):
            self.assertIn(label, qml_source)

    def test_dialogs_use_opaque_panel_and_modal_scrim(self):
        theme = (QML / "Theme.qml").read_text(encoding="utf-8")
        main = MAIN_QML.read_text(encoding="utf-8")
        confirm = CONFIRM_DIALOG_QML.read_text(encoding="utf-8")

        self.assertIn("readonly property color dialogPanel", theme)
        self.assertIn("readonly property color dialogScrim", theme)

        for dialog_id in (
            "firstRunSafetyGuideDialog",
            "trayCloseHintDialog",
            "reminderDialog",
            "liveModeConfirmDialog",
        ):
            dialog_start = main.index(f"id: {dialog_id}")
            next_dialog = main.find("\n    Dialog {", dialog_start + 1)
            confirm_dialog = main.find("\n    ConfirmDialog {", dialog_start + 1)
            candidates = [index for index in (next_dialog, confirm_dialog) if index != -1]
            dialog_section = main[dialog_start:min(candidates) if candidates else len(main)]
            self.assertIn("Overlay.modal: Rectangle", dialog_section)
            self.assertIn("color: Theme.dialogScrim", dialog_section)
            self.assertIn("color: Theme.dialogPanel", dialog_section)

        self.assertIn("Overlay.modal: Rectangle", confirm)
        self.assertIn("color: Theme.dialogScrim", confirm)
        self.assertIn("color: Theme.dialogPanel", confirm)

    def test_buttons_and_action_tiles_guard_against_text_overflow(self):
        button = NEON_BUTTON_QML.read_text(encoding="utf-8")
        action_tile = ACTION_TILE_QML.read_text(encoding="utf-8")

        self.assertIn("clip: true", button)
        self.assertIn("maximumLineCount: 1", button)
        self.assertIn("elide: Text.ElideRight", button)

        self.assertIn("Layout.maximumWidth", action_tile)
        self.assertGreaterEqual(action_tile.count("fontSizeMode: Text.HorizontalFit"), 2)
        self.assertGreaterEqual(action_tile.count("maximumLineCount: 1"), 2)
        self.assertGreaterEqual(action_tile.count("elide: Text.ElideRight"), 2)

    def test_dense_task_and_diagnostics_actions_wrap_instead_of_overflowing(self):
        main = MAIN_QML.read_text(encoding="utf-8")
        task_queue = TASK_QUEUE_DASHBOARD_QML.read_text(encoding="utf-8")

        queue_index = task_queue.index("id: taskQueueDashboard")
        queue_section = task_queue[queue_index:]
        self.assertIn("id: taskQueueActions", queue_section)
        self.assertIn("Flow {", queue_section)
        self.assertIn("height: modelData.status === \"failed\" ? 118 : 90", queue_section)

        trigger_log_index = main.index('Text { Layout.fillWidth: true; text: "触发日志"')
        trigger_log_section = main[trigger_log_index:main.index("filteredLogText", trigger_log_index)]
        self.assertIn("id: supportActionGrid", trigger_log_section)
        self.assertIn("GridLayout {", trigger_log_section)
        self.assertIn("maximumLineCount", trigger_log_section)

    def test_settings_help_text_wraps_inside_rows(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        timeout_help_index = main.index("1-300 秒")
        timeout_row = main[main.rfind("RowLayout {", 0, timeout_help_index):main.find("\n                    RowLayout {", timeout_help_index)]
        self.assertIn("wrapMode: Text.WordWrap", timeout_row)
        self.assertIn("maximumLineCount: 2", timeout_row)

    def test_theme_defines_all_referenced_visual_tokens(self):
        theme = (QML / "Theme.qml").read_text(encoding="utf-8")
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertIn("readonly property color e5BorderBlue", theme)
        self.assertIn("Theme.e5BorderBlue", main)

    def test_theme_does_not_keep_unused_decorative_tokens(self):
        theme = (QML / "Theme.qml").read_text(encoding="utf-8")

        for token in ("e5Purple", "glowPink", "glowPurple", "floatVerySlow", "twinkleSlow", "floatSlow"):
            self.assertNotIn(token, theme)

    def test_visual_system_uses_functional_accents_instead_of_neon_pink_purple(self):
        theme = (QML / "Theme.qml").read_text(encoding="utf-8")
        qml_source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                MAIN_QML,
                NEON_BUTTON_QML,
                ACTION_TILE_QML,
                CONFIRM_DIALOG_QML,
                QML / "components" / "FluentSwitch.qml",
            )
        )

        for token in (
            "borderPink",
            "secondary",
            "e5Pink",
            "e5BorderPink",
            "e5BorderPurple",
            "glowBlue",
        ):
            self.assertNotIn(f"readonly property color {token}", theme)
            self.assertNotIn(f"Theme.{token}", qml_source)

        for decorative_color in ("#AAFF8ACF", "#B779FF", "#FF8ACF", "#FF7AB6", "#BBFF6FD8", "#AA9B5CFF", "#2458C7E8"):
            self.assertNotIn(decorative_color, theme)

        self.assertIn('readonly property color accent: "#7DFFC4"', theme)
        self.assertIn("readonly property color selectedOverlay", theme)
        self.assertIn("readonly property color checkedTrack", theme)
        self.assertIn("Theme.borderStrong", qml_source)
        self.assertIn("Theme.selectedOverlay", qml_source)
        self.assertIn("Theme.checkedTrack", qml_source)

    def test_background_decoration_is_restrained_for_readability(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        self.assertNotIn("model: 12", main)
        background_section = main[main.index("// Quiet depth layers behind the work surface."):main.index("NeonCard {\n        id: appShell")]
        self.assertNotIn("SequentialAnimation on opacity", background_section)
        self.assertNotIn("SequentialAnimation on y", background_section)
        self.assertNotIn("id: orb", main)
        self.assertNotIn("model: 42", main)
        self.assertIn("id: panelWashTop", main)
        self.assertIn("id: panelWashBottom", main)
        self.assertNotIn("NumberAnimation { from: 0.10; to: 0.58", main)

    def test_settings_inline_help_text_is_clamped(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        reminder_help_index = main.index("逗号分隔，例如 10,5,1")
        reminder_row = main[main.rfind("RowLayout {", 0, reminder_help_index):main.find("\n                    RowLayout {", reminder_help_index)]
        self.assertIn("Layout.fillWidth: true", reminder_row)
        self.assertIn("wrapMode: Text.WordWrap", reminder_row)
        self.assertIn("maximumLineCount: 2", reminder_row)

    def test_settings_page_scrolls_instead_of_overflowing_window(self):
        main = MAIN_QML.read_text(encoding="utf-8")

        settings_index = main.index("// Settings page")
        settings_section = main[settings_index:main.index("Window {", settings_index)]
        self.assertIn("id: settingsScroll", settings_section)
        self.assertIn("contentWidth: availableWidth", settings_section)
        self.assertIn("width: settingsScroll.availableWidth", settings_section)
        self.assertIn("bottomPadding: 24", settings_section)


if __name__ == "__main__":
    unittest.main()
