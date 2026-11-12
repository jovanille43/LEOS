"""Contract tests for Gaming Mode quick-panel gamepad navigation."""

from pathlib import Path
import unittest


class GamingQuickPanelGamepadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qml = (
            Path(__file__).resolve().parents[1] / "gaming/qml/Main.qml"
        ).read_text(encoding="utf-8")

    def test_quick_panel_has_a_bounded_action_sequence(self):
        self.assertIn("function quickPanelActionCount()", self.qml)
        self.assertIn("return leos.availablePowerProfiles.length + 3", self.qml)
        self.assertIn("(quickPanelFocusIndex + delta + count) % count", self.qml)

    def test_gamepad_directions_and_confirm_operate_quick_panel(self):
        self.assertIn('if (quickPanel.visible) {', self.qml)
        self.assertIn("moveQuickPanelFocus(action)", self.qml)
        self.assertIn("activateQuickPanelFocus()", self.qml)

    def test_quick_panel_actions_cover_mangohud_profiles_and_exit(self):
        self.assertIn("leos.setMangoHudEnabled(!leos.mangoHudEnabled)", self.qml)
        self.assertIn("powerProfileDialog.open()", self.qml)
        self.assertIn("returnDialog.open()", self.qml)
        self.assertIn("quickPanel.visible = false", self.qml)

    def test_power_profile_confirmation_is_gamepad_operable(self):
        self.assertIn("if (powerProfileDialog.visible)", self.qml)
        self.assertIn("powerProfileDialog.close()", self.qml)
        self.assertIn("leos.applyPowerProfile(pendingPowerProfile)", self.qml)

    def test_opening_quick_panel_resets_focus(self):
        self.assertGreaterEqual(
            self.qml.count("quickPanelFocusIndex = 0"), 2
        )

    def test_focus_is_visibly_indicated_on_quick_panel_controls(self):
        self.assertIn("window.quickPanelFocusIndex === 0", self.qml)
        self.assertIn("window.quickPanelFocusIndex === index + 1", self.qml)
        self.assertIn(
            "window.quickPanelFocusIndex === leos.availablePowerProfiles.length + 1",
            self.qml,
        )


if __name__ == "__main__":
    unittest.main()
