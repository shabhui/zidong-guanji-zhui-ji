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
        mascot_index = main.index("StarryMascot {", power_index)
        power_section = main[power_index:mascot_index]

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


if __name__ == "__main__":
    unittest.main()
