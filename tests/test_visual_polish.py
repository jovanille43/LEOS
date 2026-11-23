"""Source-level regression checks for the refined LEOS visual hierarchy."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class VisualPolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selector = (ROOT / "launcher/qml/ModeSelector.qml").read_text(encoding="utf-8")
        cls.gaming = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")

    def test_mode_cards_use_the_live_a_b_identity_and_smooth_focus_feedback(self):
        for token in (
            "window.colorA.r", "window.colorB.r",
            "desktopCard.hovered", "gamingCard.hovered",
            "Easing.OutCubic", "01  /  ESPACE DE TRAVAIL", "02  /  IMMERSION",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.selector)

    def test_gaming_handoff_uses_graphite_with_subtle_user_selected_glows(self):
        self.assertIn('GradientStop { position: 0.0; color: "#1A1A1A" }', self.selector)
        self.assertIn('GradientStop { position: 0.52; color: "#080808" }', self.selector)
        self.assertIn("color: window.colorA", self.selector)
        self.assertIn("color: window.colorB", self.selector)
        self.assertNotIn('color: "#15111B"', self.selector)

    def test_game_cards_have_better_artwork_ratio_and_live_a_b_selection(self):
        self.assertIn("cellHeight: 208", self.gaming)
        self.assertIn("Layout.preferredWidth: 96", self.gaming)
        self.assertIn("Layout.preferredHeight: 136", self.gaming)
        self.assertIn("window.accentA.r, window.accentA.g, window.accentA.b", self.gaming)
        self.assertIn("gameCard.activeFocus ? window.focusColor", self.gaming)
        self.assertIn("Behavior on scale", self.gaming)

    def test_gaming_particles_remain_the_live_a_b_ambient_layer(self):
        self.assertIn("colorA: window.accentA", self.gaming)
        self.assertIn("colorB: window.accentB", self.gaming)
        self.assertIn("active: leos.animationsEnabled && !window.returningToDesktop", self.gaming)


if __name__ == "__main__":
    unittest.main()
