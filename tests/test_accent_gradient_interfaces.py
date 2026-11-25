"""Regression checks for the shared, visible LEOS A/B gradient treatment."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AccentGradientInterfaceTests(unittest.TestCase):
    def _read(self, relative_path):
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def _assert_horizontal_ab_gradient(self, source, component):
        with self.subTest(component=component):
            self.assertIn("orientation: Gradient.Horizontal", source)
            self.assertIn("GradientStop { position: 0.0; color: window.accentA }", source)
            self.assertIn("GradientStop { position: 1.0; color: window.accentB }", source)

    def test_desktop_launcher_blends_both_accents_across_its_backdrop(self):
        source = self._read("desktop/qml/Menu.qml")
        self._assert_horizontal_ab_gradient(source, "Desktop launcher")
        self.assertIn("opacity: 0.055", source)

    def test_gaming_blends_both_accents_across_its_backdrop(self):
        source = self._read("gaming/qml/Main.qml")
        self._assert_horizontal_ab_gradient(source, "Gaming")
        self.assertIn("opacity: 0.045", source)

    def test_control_center_blends_both_accents_and_keeps_neutral_surfaces(self):
        source = self._read("control_center/qml/Main.qml")
        self._assert_horizontal_ab_gradient(source, "Control Center")
        self.assertIn("color: window.themeColors.surface", source)
        self.assertIn("color: window.color", source)

    def test_theme_editor_preview_tracks_unsaved_a_and_b_choices(self):
        source = self._read("control_center/qml/Main.qml")
        self.assertIn("Layout.preferredHeight: 20", source)
        self.assertIn("color: Qt.color(window.draftColorA)", source)
        self.assertIn("color: Qt.color(window.draftColorB)", source)
        self.assertIn('text: "ENREGISTRER LE DÉGRADÉ A/B"', source)


if __name__ == "__main__":
    unittest.main()
