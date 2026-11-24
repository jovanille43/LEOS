"""Tests for LEOS interface theme palettes."""

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from desktop.themes import (
    DEFAULT_THEME,
    REQUIRED_TOKENS,
    THEME_PALETTES,
    palette_for_theme,
    validate_palette,
)


def _relative_luminance(color: str) -> float:
    channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
        for value in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(foreground: str, background: str) -> float:
    first = _relative_luminance(foreground)
    second = _relative_luminance(background)
    return (max(first, second) + 0.05) / (min(first, second) + 0.05)


class DesktopThemeTests(unittest.TestCase):
    def test_all_builtin_palettes_have_complete_valid_tokens(self):
        self.assertEqual(
            set(THEME_PALETTES),
            {"leos-original", "light", "cyan", "magenta", "gaming"},
        )
        for palette in THEME_PALETTES.values():
            self.assertEqual(set(palette), REQUIRED_TOKENS)
            self.assertTrue(validate_palette(palette))

    def test_text_and_muted_text_meet_wcag_aa_on_all_palette_surfaces(self):
        surfaces = ("background", "surface", "surface_elevated")
        text_tokens = ("text", "muted_text")
        for theme_name, palette in THEME_PALETTES.items():
            for text_token in text_tokens:
                for surface_token in surfaces:
                    with self.subTest(
                        theme=theme_name,
                        text=text_token,
                        surface=surface_token,
                    ):
                        self.assertGreaterEqual(
                            _contrast_ratio(palette[text_token], palette[surface_token]),
                            4.5,
                        )

    def test_unknown_theme_falls_back_to_leos_original(self):
        self.assertEqual(palette_for_theme("not-a-theme"), THEME_PALETTES[DEFAULT_THEME])

    def test_palette_is_a_defensive_copy(self):
        palette = palette_for_theme("leos-original")
        palette["background"] = "#FFFFFF"
        self.assertEqual(
            palette_for_theme("leos-original")["background"],
            THEME_PALETTES[DEFAULT_THEME]["background"],
        )

    def test_invalid_or_incomplete_custom_palette_is_rejected(self):
        self.assertFalse(validate_palette(None))
        self.assertFalse(validate_palette({"background": "#FFFFFF"}))
        invalid = palette_for_theme(DEFAULT_THEME)
        invalid["accent_primary"] = "cyan"
        self.assertFalse(validate_palette(invalid))

    def test_control_center_is_bound_to_live_theme_tokens(self):
        root = Path(__file__).resolve().parents[1]
        qml = (root / "control_center" / "qml" / "Main.qml").read_text(encoding="utf-8")
        controller = (root / "control_center" / "controller.py").read_text(encoding="utf-8")
        self.assertIn("property var themeColors: controlCenter.themePalette", qml)
        self.assertIn("color: themeColors.background", qml)
        self.assertIn("window.themeColors.accent_primary", qml)
        self.assertIn("property color accentA: themeColors.accent_primary", qml)
        self.assertIn("property color cyan: themeColors.accent_primary_text", qml)
        self.assertIn("def themePalette(self)", controller)
        self.assertIn("palette_for_colors(", controller)
        self.assertIn("theme_color_a", controller)
        self.assertIn("theme_color_b", controller)
        self.assertNotIn("#121720", qml)
        self.assertNotIn("#293342", qml)

    def test_control_center_exposes_free_a_b_color_editors(self):
        root = Path(__file__).resolve().parents[1]
        qml = (root / "control_center" / "qml" / "Main.qml").read_text(encoding="utf-8")
        controller = (root / "control_center" / "controller.py").read_text(encoding="utf-8")
        self.assertIn("id: themeColorADialog", qml)
        self.assertIn("id: themeColorBDialog", qml)
        self.assertIn("controlCenter.setThemeColors(", qml)
        self.assertIn("def setThemeColors(self, color_a: str, color_b: str)", controller)
        self.assertNotIn('model: ["LEOS Original", "Light", "Cyan", "Magenta", "Gaming"]', qml)

    def test_all_shared_combo_selectors_refresh_after_external_settings_changes(self):
        root = Path(__file__).resolve().parents[1]
        qml = (root / "control_center" / "qml" / "Main.qml").read_text(encoding="utf-8")
        for expression in (
            "desktopLayoutBox.currentIndex =",
            "dockPositionBox.currentIndex =",
            "dockAlignmentBox.currentIndex =",
            "profileBox.currentIndex =",
            "notificationDurationBox.currentIndex =",
            "notificationPriorityBox.currentIndex =",
        ):
            with self.subTest(expression=expression):
                self.assertIn(expression, qml)


    def test_plasma_style_covers_widget_headers_task_states_and_panel_controls(self):
        root = Path(__file__).resolve().parents[1] / "plasma-theme" / "leos" / "widgets"
        positions = {
            "topleft", "top", "topright", "left", "center",
            "right", "bottomleft", "bottom", "bottomright",
        }
        expected = {
            "plasmoidheading.svg": {
                f"{prefix}-{position}"
                for prefix in ("header", "footer")
                for position in positions
            } | {
                "hint-top-margin", "hint-right-margin",
                "hint-bottom-margin", "hint-left-margin",
                "hint-stretch-borders",
            },
            "tasks.svg": {
                f"{state}-{position}"
                for state in ("normal", "focus", "hover", "attention", "minimized")
                for position in positions
            } | {"hint-stretch-borders", "hint-compose-over-border"},
            "containment-controls.svg": {
                f"{direction}-{kind}{position}"
                for direction in ("north", "east", "south", "west")
                for kind in ("", "minslider-", "maxslider-", "offsetslider-")
                for position in positions
            } | {"horizontal-centerindicator", "vertical-centerindicator"},
        }
        for filename, required_ids in expected.items():
            with self.subTest(filename=filename):
                path = root / filename
                self.assertTrue(path.is_file(), f"Missing Plasma Style asset: {filename}")
                document = ET.parse(path)
                elements = list(document.getroot().iter())
                identifiers = [element.attrib["id"] for element in elements if "id" in element.attrib]
                self.assertEqual(len(identifiers), len(set(identifiers)), "SVG element IDs must be unique")
                self.assertTrue(required_ids.issubset(set(identifiers)))
                accent = next((element for element in elements if element.attrib.get("id") == "leosAccent"), None)
                self.assertIsNotNone(accent, "The A/B recoloring gradient must be present")
                stops = [element.attrib.get("stop-color") for element in accent.iter()
                         if element.tag.endswith("stop")]
                self.assertEqual(stops[0], "#00D9FF")
                self.assertEqual(stops[-1], "#E33BFF")



if __name__ == "__main__":
    unittest.main()
