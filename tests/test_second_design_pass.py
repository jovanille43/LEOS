"""Regression checks for the second LEOS interface design pass."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SecondDesignPassTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.control = (ROOT / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        cls.controllers = (ROOT / "controller_center/qml/Main.qml").read_text(encoding="utf-8")
        cls.gaming = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")

    def test_control_center_navigation_has_a_live_ab_active_state(self):
        self.assertIn("settingsNavigationButton.hovered", self.control)
        self.assertIn("window.accentA.r, window.accentA.g, window.accentA.b", self.control)
        self.assertIn("window.accentB.r, window.accentB.g, window.accentB.b", self.control)
        self.assertIn("window.selectedPage === modelData.page ? Font.DemiBold", self.control)
        self.assertIn("width: window.selectedPage === modelData.page ? 3 : 0", self.control)

    def test_control_center_uses_a_shared_ab_brand_divider_and_neutral_glow(self):
        self.assertIn("CENTRE DE CONTRÔLE", self.control)
        self.assertIn("window.accentA", self.control)
        self.assertIn("window.accentB", self.control)
        self.assertIn("opacity: 0.045", self.control)
        self.assertIn("opacity: 0.04", self.control)
        self.assertIn("PRÉFÉRENCES UTILISATEUR", self.control)
        self.assertIn("source: leosTheme.desktopLogoUrl", self.control)

    def test_controller_center_uses_live_ab_surfaces_and_a_clear_input_readout(self):
        self.assertIn("window.accentA.r, window.accentA.g, window.accentA.b", self.controllers)
        self.assertIn("DERNIÈRE ENTRÉE", self.controllers)
        self.assertIn("font.weight: Font.DemiBold", self.controllers)
        self.assertIn("CENTRE DES MANETTES", self.controllers)
        self.assertIn("source: leosTheme.desktopLogoUrl", self.controllers)
        self.assertIn("Layout.preferredHeight: 116", self.controllers)
        self.assertIn("window.accentB.r, window.accentB.g, window.accentB.b", self.controllers)

    def test_gaming_detail_status_and_launch_action_have_distinct_visual_priority(self):
        self.assertIn("installStatusText", self.gaming)
        self.assertIn('window.selectedInstallStatus === "Fichiers absents"', self.gaming)
        self.assertIn("launchSelectedGameButton.enabled ? 0.2 : 0.035", self.gaming)
        self.assertIn("Détails du jeu sélectionné", self.gaming)
        self.assertIn("window.accentB.r, window.accentB.g, window.accentB.b", self.gaming)


if __name__ == "__main__":
    unittest.main()
