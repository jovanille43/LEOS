"""Regression tests for freely selected LEOS accent colors."""

import json
import re
import tempfile
import unittest
from pathlib import Path
from datetime import datetime

from leos_core.settings import SettingsStore
from desktop.themes import (DEFAULT_COLOR_A, DEFAULT_COLOR_B, SOURCE_COLOR_A, SOURCE_COLOR_B, normalize_color, palette_for_colors, resolve_appearance_mode, validate_palette)


class DynamicThemeTests(unittest.TestCase):
    def test_unconfigured_preview_is_neutral_not_the_historical_source_gradient(self):
        self.assertNotEqual(DEFAULT_COLOR_A, SOURCE_COLOR_A)
        self.assertNotEqual(DEFAULT_COLOR_B, SOURCE_COLOR_B)
        for color in (DEFAULT_COLOR_A, DEFAULT_COLOR_B):
            self.assertEqual(color[1:3], color[3:5])
            self.assertEqual(color[3:5], color[5:7])

    def test_dark_and_light_material_surfaces_are_neutral_grayscale(self):
        for appearance in ("dark", "light"):
            with self.subTest(appearance=appearance):
                palette = palette_for_colors("#E58A3A", "#4F75D5", appearance=appearance)
                for token in ("background", "surface", "surface_elevated", "border", "text", "muted_text"):
                    color = palette[token]
                    self.assertEqual(color[1:3], color[3:5], f"{appearance} {token} red/green differ")
                    self.assertEqual(color[3:5], color[5:7], f"{appearance} {token} green/blue differ")
                self.assertEqual(palette["accent_primary"], "#E58A3A")
                self.assertEqual(palette["accent_secondary"], "#4F75D5")

    def test_particle_backdrop_uses_neutral_fallbacks_and_bounded_density(self):
        root = Path(__file__).resolve().parents[1]
        backdrop = (root / "branding" / "qml" / "ParticleBackdrop.qml").read_text(encoding="utf-8")
        gaming = (root / "gaming" / "qml" / "Main.qml").read_text(encoding="utf-8")
        self.assertIn('property color colorA: "#A0A0A0"', backdrop)
        self.assertIn('property color colorB: "#D0D0D0"', backdrop)
        self.assertIn("property int particleCount: 42", backdrop)
        self.assertIn("particleOpacity: 0.30", gaming)
        self.assertIn("model: 16", gaming)
        self.assertIn("window.accentB", gaming)

    def test_primary_interfaces_do_not_use_microtext_below_ten_pixels(self):
        root = Path(__file__).resolve().parents[1]
        qml_paths = (
            "control_center/qml/Main.qml",
            "launcher/qml/ModeSelector.qml",
            "desktop/qml/Menu.qml",
            "desktop/qml/Notifications.qml",
            "shop/qml/Main.qml",
        )
        for relative in qml_paths:
            with self.subTest(interface=relative):
                content = (root / relative).read_text(encoding="utf-8")
                sizes = [
                    int(value)
                    for value in re.findall(r"font\.pixelSize\s*:\s*(\d+)", content)
                ]
                self.assertTrue(sizes, f"{relative} has no statically sized text")
                self.assertFalse(
                    [size for size in sizes if size < 10],
                    f"{relative} still contains text smaller than 10 px",
                )

    def test_gaming_uses_selected_accents_and_shared_neutral_surfaces(self):
        root = Path(__file__).resolve().parents[1]
        qml = (root / "gaming" / "qml" / "Main.qml").read_text(encoding="utf-8")
        self.assertIn("color: window.accentA; opacity: 0.085", qml)
        self.assertIn("color: window.accentB; opacity: 0.07", qml)
        for legacy in ('#102331', '#2a1232', '#123847', '#17313d'):
            self.assertNotIn(legacy, qml)
        self.assertIn("window.themeColors.surface_elevated", qml)
        self.assertIn("window.themeColors.border", qml)

    def test_cinematic_wallpapers_keep_materials_neutral_for_a_b_recoloring(self):
        root = Path(__file__).resolve().parents[1]
        for filename in ("desktop-leos.svg", "gaming-leos.svg"):
            wallpaper = (root / "branding" / "wallpapers" / filename).read_text(encoding="utf-8")
            colors = {color.upper() for color in re.findall(r"#[0-9A-Fa-f]{6}(?=[^0-9A-Fa-f]|$)", wallpaper)}
            self.assertTrue({"#00D9FF", "#E33BFF"}.isdisjoint(colors))
            for color in colors:
                self.assertEqual(
                    color[1:3], color[3:5],
                    f"{filename} contains a non-neutral material color: {color}",
                )
                self.assertEqual(
                    color[3:5], color[5:7],
                    f"{filename} contains a non-neutral material color: {color}",
                )

    def test_light_and_dark_palettes_keep_user_accents_unchanged(self):
        dark = palette_for_colors("#FF8800", "#0055CC", appearance="dark")
        light = palette_for_colors("#FF8800", "#0055CC", appearance="light")
        self.assertNotEqual(dark["background"], light["background"])
        self.assertGreaterEqual(
            int(light["background"][1:3], 16),
            int(dark["background"][1:3], 16),
        )
        for key in ("accent_primary", "accent_secondary"):
            self.assertEqual(dark[key], light[key])

    def test_automatic_appearance_uses_local_day_and_night_boundaries(self):
        self.assertEqual(resolve_appearance_mode("auto", datetime(2026, 11, 24, 6, 59)), "dark")
        self.assertEqual(resolve_appearance_mode("auto", datetime(2026, 11, 24, 7, 0)), "light")
        self.assertEqual(resolve_appearance_mode("auto", datetime(2026, 11, 24, 18, 59)), "light")
        self.assertEqual(resolve_appearance_mode("auto", datetime(2026, 11, 24, 19, 0)), "dark")

    def test_control_center_exposes_all_three_appearance_modes(self):
        root = Path(__file__).resolve().parents[1]
        controller = (root / "control_center" / "controller.py").read_text(encoding="utf-8")
        qml = (root / "control_center" / "qml" / "Main.qml").read_text(encoding="utf-8")
        self.assertIn("def setAppearanceMode(self, mode: str)", controller)
        self.assertIn("def appearanceMode(self)", controller)
        self.assertIn("def effectiveAppearance(self)", controller)
        for mode in ('"dark"', '"light"', '"auto"'):
            self.assertIn(f"setAppearanceMode({mode})", qml)

    def test_selected_endpoints_are_never_replaced_for_low_contrast(self):
        palette = palette_for_colors("#111111", "#111111")
        self.assertEqual(palette["accent_primary"], "#111111")
        self.assertEqual(palette["accent_secondary"], "#111111")
        self.assertEqual(palette["accent_primary_text"], palette["text"])
        self.assertEqual(palette["accent_secondary_text"], palette["text"])
        self.assertTrue(validate_palette(palette))

    def test_distinct_user_colors_remain_exact_palette_endpoints(self):
        palette = palette_for_colors("#FF8800", "#0055CC")
        self.assertEqual(palette["accent_primary"], "#FF8800")
        self.assertEqual(palette["accent_secondary"], "#0055CC")
        self.assertTrue(validate_palette(palette))

    def test_legacy_unconfigured_settings_migrate_to_neutral_preview(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text(json.dumps({
                "theme_color_a": "#00D9FF",
                "theme_color_b": "#E33BFF",
                "theme_colors_configured": False,
            }), encoding="utf-8")
            settings = SettingsStore(path=path)
            self.assertEqual(
                settings.snapshot(("theme_color_a", "theme_color_b")),
                (DEFAULT_COLOR_A, DEFAULT_COLOR_B),
            )

    def test_hex_colors_are_trimmed_and_normalized(self):
        self.assertEqual(normalize_color(" #ab12EF "), "#AB12EF")

    def test_invalid_hex_values_are_rejected(self):
        for value in ("cyan", "#123", "#GG0000", "#11223344", ""):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_color(value)


if __name__ == "__main__":
    unittest.main()
