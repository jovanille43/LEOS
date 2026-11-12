"""Accessibility, typography, and controller-hint contracts for Gaming Mode."""

from pathlib import Path
import re
import unittest

from gaming.backend.gamepad import gamepad_button_legend


ROOT = Path(__file__).resolve().parents[1]


class GamingAccessibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qml = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        cls.controller = (
            ROOT / "gaming/backend/controller.py"
        ).read_text(encoding="utf-8")

    def test_game_cards_have_accessible_names_and_selection_state(self):
        self.assertIn("Accessible.role: Accessible.Button", self.qml)
        self.assertIn("Accessible.name: gameCard.title", self.qml)
        self.assertIn(
            "Accessible.selected: window.selectedIndex === gameCard.index",
            self.qml,
        )
        self.assertIn("Accessible.description:", self.qml)

    def test_library_grid_and_category_buttons_are_named(self):
        self.assertIn("Accessible.role: Accessible.List", self.qml)
        self.assertIn('Accessible.name: "Bibliothèque de jeux"', self.qml)
        self.assertIn("Accessible.name: categoryButton.text", self.qml)

    def test_search_field_is_exposed_as_editable_text(self):
        self.assertIn("Accessible.role: Accessible.EditableText", self.qml)
        self.assertIn('Accessible.name: "Rechercher un jeu"', self.qml)

    def test_quick_panel_is_exposed_as_a_named_group(self):
        self.assertIn("Accessible.role: Accessible.Grouping", self.qml)
        self.assertIn('Accessible.name: "Panneau rapide Gaming"', self.qml)

    def test_empty_state_and_status_message_are_announced(self):
        self.assertIn("Accessible.role: Accessible.StaticText", self.qml)
        self.assertIn("Accessible.name: text", self.qml)
        self.assertIn('id: statusText', self.qml)
        self.assertIn("Accessible.description:", self.qml)

    def test_typography_uses_readable_tokens_and_no_sub_12px_literals(self):
        self.assertIn("property int fontMicro: 12", self.qml)
        self.assertIn("property int fontBody: 16", self.qml)
        self.assertIn("property int fontTitle: 25", self.qml)
        pixel_sizes = [
            int(value)
            for value in re.findall(r"font\\.pixelSize\\s*:\\s*(\\d+)", self.qml)
        ]
        self.assertFalse(
            [value for value in pixel_sizes if value < 12],
            "Gaming QML still contains text smaller than 12 px",
        )

    def test_focus_color_is_separate_from_selection_and_favorite_accents(self):
        self.assertIn('property color focusColor: "#ffffff"', self.qml)
        self.assertIn("window.focusColor", self.qml)
        self.assertIn('color: window.magenta', self.qml)

    def test_controller_legend_is_exposed_to_qml(self):
        self.assertIn("def gamepadButtonLegend", self.controller)
        self.assertIn("text: leos.gamepadButtonLegend", self.qml)
        self.assertIn("ENTRÉE / ESPACE", self.qml)
        self.assertIn("ÉCHAP", self.qml)
        self.assertIn("F1", self.qml)

    def test_button_legend_matches_standard_and_named_controller_layouts(self):
        self.assertEqual(
            gamepad_button_legend("xbox"),
            "A · VALIDER   B · RETOUR",
        )
        self.assertEqual(
            gamepad_button_legend("nintendo"),
            "A · VALIDER   B · RETOUR",
        )
        self.assertEqual(
            gamepad_button_legend("playstation"),
            "× · VALIDER   ○ · RETOUR",
        )
        self.assertEqual(
            gamepad_button_legend("standard"),
            "BOUTON DU BAS · VALIDER   BOUTON DROIT · RETOUR",
        )
        self.assertEqual(
            gamepad_button_legend("custom"),
            "BOUTON DU BAS · VALIDER   BOUTON DROIT · RETOUR",
        )


if __name__ == "__main__":
    unittest.main()
