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


if __name__ == "__main__":
    unittest.main()
