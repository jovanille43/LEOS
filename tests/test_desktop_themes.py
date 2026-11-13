"""Tests for LEOS interface theme palettes."""

import unittest
from pathlib import Path

from desktop.themes import (
    DEFAULT_THEME,
    REQUIRED_TOKENS,
    custom_colors_from_theme,
    custom_theme_id,
    is_valid_theme_id,
    THEME_PALETTES,
    palette_for_theme,
    theme_options,
    visual_tokens_for_theme,
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
            {
                "leos-original", "light", "cyan", "magenta", "gaming",
                "emerald-gold", "yellow-red", "electric-blue-orange", "violet-gold",
            },
        )
        for palette in THEME_PALETTES.values():
            self.assertEqual(set(palette), REQUIRED_TOKENS)
            self.assertTrue(validate_palette(palette))

    def test_all_themes_keep_the_same_neutral_leos_design_surfaces(self):
        base = THEME_PALETTES[DEFAULT_THEME]
        neutral_tokens = (
            "background",
            "surface",
            "surface_elevated",
            "border",
            "text",
            "muted_text",
        )
        for theme, palette in THEME_PALETTES.items():
            for token in neutral_tokens:
                with self.subTest(theme=theme, token=token):
                    self.assertEqual(palette[token], base[token])

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

    def test_theme_catalog_exposes_two_distinct_accents_for_every_theme(self):
        options = theme_options()
        self.assertEqual({item["id"] for item in options}, set(THEME_PALETTES))
        for item in options:
            with self.subTest(theme=item["id"]):
                self.assertRegex(item["accent_primary"], r"^#[0-9A-Fa-f]{6}$")
                self.assertRegex(item["accent_secondary"], r"^#[0-9A-Fa-f]{6}$")
                self.assertNotEqual(
                    item["accent_primary"].lower(),
                    item["accent_secondary"].lower(),
                )

    def test_visual_tokens_derive_both_glows_and_a_two_color_gradient(self):
        tokens = visual_tokens_for_theme(DEFAULT_THEME)
        self.assertEqual(tokens["accent_primary"], THEME_PALETTES[DEFAULT_THEME]["accent_primary"])
        self.assertEqual(tokens["accent_secondary"], THEME_PALETTES[DEFAULT_THEME]["accent_secondary"])
        for key in (
            "accent_primary_glow",
            "accent_secondary_glow",
            "accent_primary_soft",
            "accent_secondary_soft",
            "accent_gradient_mid",
        ):
            self.assertRegex(tokens[key], r"^#[0-9A-Fa-f]{6}$")
        self.assertNotEqual(tokens["accent_primary_glow"], tokens["accent_secondary_glow"])

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
        self.assertIn("property color primaryAccent: themeColors.accent_primary", qml)
        self.assertIn("property color primaryGlow: themeColors.accent_primary_glow", qml)
        self.assertIn("property color secondaryGlow: themeColors.accent_secondary_glow", qml)
        self.assertIn("def themePalette(self)", controller)
        self.assertIn("visual_tokens_for_theme(self.theme)", controller)
        self.assertNotIn("#121720", qml)
        self.assertNotIn("#293342", qml)

    def test_theme_selector_refreshes_when_shared_settings_change(self):
        root = Path(__file__).resolve().parents[1]
        qml = (root / "control_center" / "qml" / "Main.qml").read_text(encoding="utf-8")
        self.assertIn("function onSettingsChanged()", qml)
        self.assertIn("model: controlCenter.themeOptions", qml)
        self.assertIn("controlCenter.themeOptions.map(option => option.id)", qml)
        self.assertIn("themeBox.currentIndex = Math.max(0, themes.indexOf(controlCenter.theme))", qml)


    def test_first_run_mode_selector_uses_the_shared_theme_manager(self):
        root = Path(__file__).resolve().parents[1]
        qml = (root / "launcher" / "qml" / "ModeSelector.qml").read_text(encoding="utf-8")
        main = (root / "launcher" / "main.py").read_text(encoding="utf-8")
        self.assertIn("themeManager.palette", qml)
        self.assertIn("themeManager.options", qml)
        self.assertIn("themeManager.setTheme(options[index].id)", qml)
        self.assertIn('setContextProperty("themeManager", theme_manager)', main)
        self.assertIn("themeSelectionComplete", qml)

    def test_all_leos_qml_apps_receive_the_shared_theme_palette(self):
        root = Path(__file__).resolve().parents[1]
        expected = {
            "gaming/qml/Main.qml": "themeManager.palette",
            "desktop/qml/Menu.qml": "themeManager.palette",
            "desktop/qml/Notifications.qml": "themeManager.palette",
            "controller_center/qml/Main.qml": "themeManager.palette",
            "shop/qml/Main.qml": "themeManager.palette",
        }
        for relative, expression in expected.items():
            with self.subTest(path=relative):
                content = (root / relative).read_text(encoding="utf-8")
                self.assertIn(expression, content)

    def test_brand_assets_are_referenced_through_theme_asset_map(self):
        root = Path(__file__).resolve().parents[1]
        selector = (root / "launcher/qml/ModeSelector.qml").read_text(encoding="utf-8")
        gaming = (root / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        control = (root / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("themeManager.assets.desktop_logo", selector)
        self.assertIn("themeManager.assets.gaming_logo", selector)
        self.assertIn("themeManager.assets.gaming_logo", gaming)
        self.assertIn("themeManager.assets.desktop_wallpaper", control)
        self.assertIn("themeManager.assets.gaming_wallpaper", control)
        self.assertIn("themeManager.assets.gaming_intro", selector)
        self.assertIn("themeManager.assets.desktop_intro", gaming)

    def test_theme_asset_worker_uses_selective_recoloring_and_original_fallbacks(self):
        root = Path(__file__).resolve().parents[1]
        assets = (root / "desktop/theme_assets.py").read_text(encoding="utf-8")
        manager = (root / "desktop/theme_manager.py").read_text(encoding="utf-8")
        self.assertIn("def recolor_hex_color(", assets)
        self.assertIn("def recolor_svg_markup(", assets)
        self.assertIn("def lut_cube_text(", assets)
        self.assertIn("lut3d=file=", assets)
        self.assertIn("Audio is preserved", assets)
        self.assertIn('"-map", "0:a?"', assets)
        self.assertIn("cached_video_paths_for_theme", manager)
        self.assertIn("start_new_session=True", manager)
        self.assertIn("official videos active", manager)

    def test_all_shared_combo_selectors_refresh_after_external_settings_changes(self):
        root = Path(__file__).resolve().parents[1]
        qml = (root / "control_center" / "qml" / "Main.qml").read_text(encoding="utf-8")
        for expression in (
            "themeBox.currentIndex =",
            "desktopLayoutBox.currentIndex =",
            "dockPositionBox.currentIndex =",
            "dockAlignmentBox.currentIndex =",
            "profileBox.currentIndex =",
            "notificationDurationBox.currentIndex =",
            "notificationPriorityBox.currentIndex =",
        ):
            with self.subTest(expression=expression):
                self.assertIn(expression, qml)


    def test_neon_palette_pairings_keep_electric_accent_values(self):
        expected = {
            "emerald-gold": ("#00F0A0", "#FFD84D"),
            "yellow-red": ("#FFF000", "#FF335A"),
            "electric-blue-orange": ("#168BFF", "#FF7A1A"),
            "violet-gold": ("#A855F7", "#FFD84D"),
        }
        for theme, pair in expected.items():
            with self.subTest(theme=theme):
                palette = THEME_PALETTES[theme]
                self.assertEqual((palette["accent_primary"], palette["accent_secondary"]), pair)

    def test_neon_halos_are_bound_to_both_accents_on_active_qml_surfaces(self):
        root = Path(__file__).resolve().parents[1]
        surfaces = (
            "launcher/qml/ModeSelector.qml",
            "gaming/qml/Main.qml",
            "control_center/qml/Main.qml",
            "desktop/qml/Menu.qml",
            "desktop/qml/Notifications.qml",
            "shop/qml/Main.qml",
        )
        for relative in surfaces:
            with self.subTest(path=relative):
                content = (root / relative).read_text(encoding="utf-8")
                self.assertIn("themeColors.accent_primary_glow", content)
                self.assertIn("themeColors.accent_secondary_glow", content)
                self.assertIn("border.color: window.primaryGlow", content)
                self.assertIn("border.color: window.secondaryGlow", content)


    def test_custom_pair_is_unrestricted_stable_and_keeps_the_neutral_design(self):
        theme = custom_theme_id("#121212", "#131313")
        self.assertEqual(theme, "custom-121212131313")
        self.assertEqual(custom_theme_id("#00D9FF", "#E33BFF"), "leos-original")
        self.assertEqual(custom_theme_id("#00f0a0", "#ffd84d"), "emerald-gold")
        self.assertTrue(is_valid_theme_id(theme))
        self.assertEqual(custom_colors_from_theme(theme), ("#121212", "#131313"))
        palette = palette_for_theme(theme)
        self.assertEqual(palette["accent_primary"], "#121212")
        self.assertEqual(palette["accent_secondary"], "#131313")
        self.assertEqual(palette["background"], THEME_PALETTES[DEFAULT_THEME]["background"])
        self.assertIn(theme, {item["id"] for item in theme_options(theme)})

    def test_low_contrast_custom_pair_is_warned_but_never_rejected(self):
        theme = custom_theme_id("#111111", "#121212")
        tokens = visual_tokens_for_theme(theme)
        self.assertTrue(tokens["contrast_warning"])
        self.assertIn("restent inchangées", tokens["contrast_warning_text"])
        self.assertEqual(tokens["accent_primary"], "#111111")
        self.assertEqual(tokens["accent_secondary"], "#121212")
        self.assertEqual(tokens["accent_primary_text"], tokens["text"])
        self.assertEqual(tokens["accent_secondary_text"], tokens["text"])
        self.assertIn("accent_primary_on_fill", tokens)
        self.assertIn("accent_secondary_on_fill", tokens)

    def test_custom_color_ids_reject_malformed_values_only(self):
        for pair in (("cyan", "#FFFFFF"), ("#FFFFF", "#000000"), (None, "#000000")):
            with self.subTest(pair=pair):
                with self.assertRaises((TypeError, ValueError)):
                    custom_theme_id(pair[0], pair[1])
        self.assertFalse(is_valid_theme_id("custom-not-a-color-pair"))

    def test_first_run_and_control_center_expose_custom_color_pickers(self):
        root = Path(__file__).resolve().parents[1]
        launcher = (root / "launcher/qml/ModeSelector.qml").read_text(encoding="utf-8")
        control = (root / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        for source in (launcher, control):
            self.assertIn("import QtQuick.Dialogs", source)
            self.assertIn("ColorDialog", source)
            self.assertIn("Couleur A · #RRGGBB", source)
            self.assertIn("Couleur B · #RRGGBB", source)
            self.assertIn("contrast_warning_text", source)
        self.assertIn("themeManager.setCustomColors", launcher)
        self.assertIn("controlCenter.setAccentColors", control)

    def test_all_leos_surfaces_use_contrast_aware_text_accent_roles(self):
        root = Path(__file__).resolve().parents[1]
        surfaces = (
            "launcher/qml/ModeSelector.qml",
            "gaming/qml/Main.qml",
            "control_center/qml/Main.qml",
            "desktop/qml/Menu.qml",
            "desktop/qml/Notifications.qml",
            "controller_center/qml/Main.qml",
            "shop/qml/Main.qml",
        )
        for relative in surfaces:
            with self.subTest(path=relative):
                content = (root / relative).read_text(encoding="utf-8")
                self.assertIn("themeColors.accent_primary_text", content)
                self.assertIn("themeColors.accent_secondary_text", content)
                self.assertIn("property color primaryTextAccent", content)
                self.assertIn("property color secondaryTextAccent", content)
                self.assertIn("window.primaryTextAccent", content)
                self.assertNotIn("color: window.primaryAccent", content)
                self.assertNotIn("color: window.secondaryAccent", content)

if __name__ == "__main__":
    unittest.main()
