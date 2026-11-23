"""Regression checks for the coherent LEOS desktop surface language."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DesktopSurfacePolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.menu = (ROOT / "desktop/qml/Menu.qml").read_text(encoding="utf-8")
        cls.notifications = (ROOT / "desktop/qml/Notifications.qml").read_text(encoding="utf-8")

    def test_application_menu_uses_neutral_layers_and_live_a_b_tile_surfaces(self):
        self.assertIn("cellWidth: 196", self.menu)
        self.assertIn("cellHeight: 126", self.menu)
        self.assertIn("window.accentA.r, window.accentA.g, window.accentA.b", self.menu)
        self.assertIn("appTile.activeFocus", self.menu)
        self.assertIn("Layout.preferredWidth: 36", self.menu)
        self.assertIn("font.pixelSize: 13", self.menu)
        self.assertIn("window.themeColors.surface", self.menu)

    def test_notifications_share_the_live_a_b_identity_and_improved_readability(self):
        self.assertIn("color: window.accentA", self.notifications)
        self.assertIn("color: window.accentB", self.notifications)
        self.assertIn("window.accentA.r, window.accentA.g, window.accentA.b", self.notifications)
        self.assertIn("font.pixelSize: 14", self.notifications)
        self.assertIn("font.pixelSize: 12", self.notifications)
        self.assertIn("radius: 14", self.notifications)


if __name__ == "__main__":
    unittest.main()
