from pathlib import Path
import unittest


APP_DIR = Path(__file__).resolve().parents[1]
QML_DIR = APP_DIR / "qml"


class V5UiArchitectureTest(unittest.TestCase):
    def test_main_uses_new_workspace_instead_of_legacy_page_tree(self):
        main = (QML_DIR / "Main.qml").read_text(encoding="utf-8")

        self.assertIn("WorkspaceV5 {", main)
        for legacy_id in (
            "overviewWorkspacePage",
            "launchAnimeSky",
            "launchCharacterArtwork",
            "timerWorkspacePage",
            "tasksWorkspacePage",
            "triggersWorkspacePage",
            "scriptWorkspacePage",
            "settingsWorkspacePage",
        ):
            self.assertNotIn(legacy_id, main)

    def test_new_workspace_is_split_into_six_independent_pages(self):
        workspace = (QML_DIR / "WorkspaceV5.qml").read_text(encoding="utf-8")
        expected_pages = (
            "OverviewPage",
            "TimerPage",
            "TasksPage",
            "TriggersPage",
            "ScriptPage",
            "SettingsPage",
        )

        for page_name in expected_pages:
            self.assertTrue((QML_DIR / "pages" / f"{page_name}.qml").exists())
            self.assertIn(f"{page_name} {{", workspace)

        self.assertIn("StackLayout", workspace)
        self.assertIn("currentIndex: root.rootWindow.currentPage", workspace)

    def test_workspace_uses_horizontal_top_navigation_without_sidebar(self):
        workspace = (QML_DIR / "WorkspaceV5.qml").read_text(encoding="utf-8")

        self.assertIn("id: topNavigation", workspace)
        self.assertIn("model: root.rootWindow.workspaceNavItems", workspace)
        self.assertIn("onClicked: root.rootWindow.selectWorkspacePage(index)", workspace)
        self.assertNotIn("id: sideBar", workspace)
        self.assertNotIn("V5NavItem {", workspace)

    def test_overview_uses_the_immersive_hero_deck_structure(self):
        overview = (QML_DIR / "pages" / "OverviewPage.qml").read_text(encoding="utf-8")

        for snippet in (
            "id: heroDeck",
            "id: heroCountdown",
            "id: characterStage",
            "id: bottomActionDock",
            'source: "../assets/wuthering-waves-official.webp"',
            'source: "../assets/feibi/cutout/base_front.png"',
            "controller.startQuickCountdown(",
            "controller.cancelCurrentTask()",
        ):
            self.assertIn(snippet, overview)

    def test_fixed_time_supports_dragging_hour_and_minute(self):
        timer = (QML_DIR / "pages" / "TimerPage.qml").read_text(encoding="utf-8")

        self.assertTrue((QML_DIR / "components" / "V5TimeSlider.qml").exists())
        for snippet in (
            "id: fixedHourSlider",
            "id: fixedMinuteSlider",
            "from: 0",
            "to: 23",
            "to: 59",
            "stepSize: 1",
            "onMoved: root.fixedHourValue = Math.round(value)",
            "onMoved: root.fixedMinuteValue = Math.round(value)",
        ):
            self.assertIn(snippet, timer)

    def test_new_pages_keep_core_user_flows_reachable(self):
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((QML_DIR / "pages").glob("*.qml"))
        )

        for call in (
            "controller.startCountdown(",
            "controller.startFixedTime(",
            "controller.applyTaskTemplate(",
            "controller.cancelCurrentTask()",
            "rootWindow.requestImmediateExecution()",
            "controller.startProcessTrigger()",
            "controller.startNetworkTrigger()",
            "controller.startIdleTrigger()",
            "controller.testScript()",
            "controller.runHealthCheck()",
        ):
            self.assertIn(call, source)

    def test_settings_page_does_not_separate_child_objects_with_semicolons(self):
        settings = (QML_DIR / "pages" / "SettingsPage.qml").read_text(encoding="utf-8")
        self.assertNotIn("}; FluentSwitch", settings)

    def test_action_tile_text_width_does_not_depend_on_its_own_parent_width(self):
        action_tile = (QML_DIR / "components" / "ActionTile.qml").read_text(encoding="utf-8")
        self.assertNotIn("Layout.maximumWidth: parent.width", action_tile)
        self.assertIn("Layout.maximumWidth: root.width - 66", action_tile)

    def test_new_pages_use_the_shared_light_input_skin(self):
        source = "\n".join(path.read_text(encoding="utf-8") for path in (QML_DIR / "pages").glob("*.qml"))
        field = (QML_DIR / "components" / "V5TextField.qml")
        self.assertTrue(field.exists())
        self.assertNotRegex(source, r"(?m)^\s*TextField\s*\{")
        self.assertRegex(source, r"(?m)^\s*V5TextField\s*\{")

    def test_advanced_scheduling_and_preferences_remain_reachable(self):
        source = "\n".join(path.read_text(encoding="utf-8") for path in (QML_DIR / "pages").glob("*.qml"))
        for snippet in (
            "controller.addFixedTimeTask(",
            "controller.reminderMinutesCsv = text",
            "controller.snoozeMinutesValue = parseInt(text)",
            "controller.taskHistoryLimit = parseInt(text)",
            "controller.musicAutoplayEnabled = checked",
            "controller.networkPollSeconds = parseInt(text)",
            "controller.idleAction = modelData.key",
        ):
            self.assertIn(snippet, source)


if __name__ == "__main__":
    unittest.main()
