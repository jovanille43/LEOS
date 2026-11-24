"""Cross-screen design-system contracts for LEOS visual consistency."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LeosVisualSystemTests(unittest.TestCase):
    def test_desktop_and_gaming_keep_a_shared_surface_language(self):
        desktop = (ROOT / "desktop/qml/Menu.qml").read_text(encoding="utf-8")
        gaming = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        for source in (desktop, gaming):
            self.assertIn("window.themeColors.surface", source)
            self.assertIn("window.themeColors.surface_elevated", source)
            self.assertIn("window.themeColors.border", source)
            self.assertIn("GradientStop { position: 0; color: window.accentA }", source)
            self.assertIn("GradientStop { position: 1; color: window.accentB }", source)

    def test_operational_screens_use_the_same_subtle_ab_highlight(self):
        screens = [
            "control_center/qml/Main.qml",
            "controller_center/qml/Main.qml",
            "desktop/qml/Notifications.qml",
        ]
        for path in screens:
            source = (ROOT / path).read_text(encoding="utf-8")
            self.assertIn("window.accentA", source)
            self.assertIn("window.accentB", source)
            self.assertIn("window.themeColors.surface", source)
            self.assertIn("window.themeColors.border", source)

    def test_notifications_and_library_artwork_have_semantic_fallbacks(self):
        notifications = (ROOT / "desktop/qml/Notifications.qml").read_text(encoding="utf-8")
        gaming = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn('visible: !isRead', notifications)
        self.assertIn("gameArtwork.status !== Image.Ready", gaming)
        self.assertIn("window.gameMonogram(gameCard.title)", gaming)


if __name__ == "__main__":
    unittest.main()
