"""Cross-application contract for the shared LEOS A/B theme."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ThemePropagationTests(unittest.TestCase):
    def test_every_leos_window_uses_the_shared_theme_palette(self):
        bindings = {
            "control_center/qml/Main.qml": "controlCenter.themePalette",
            "controller_center/qml/Main.qml": "controllerCenter.themePalette",
            "desktop/qml/Menu.qml": "applicationCatalog.themePalette",
            "desktop/qml/Notifications.qml": "notificationModel.themePalette",
            "gaming/qml/Main.qml": "leos.themePalette",
            "launcher/qml/ModeSelector.qml": "modeSelectorController.themePalette",
            "shop/qml/Main.qml": "store.themePalette",
        }
        for relative_path, binding in bindings.items():
            with self.subTest(path=relative_path):
                source = (ROOT / relative_path).read_text(encoding="utf-8")
                self.assertIn(binding, source)
                self.assertIn("accent_primary", source)
                self.assertIn("accent_secondary", source)
                self.assertNotIn("property color cyan:", source)
                self.assertNotIn("property color magenta:", source)
                self.assertNotIn("window.cyan", source)
                self.assertNotIn("window.magenta", source)

    def test_auxiliary_applications_refresh_cross_process_theme_changes(self):
        for relative_path in (
            "controller_center/controller.py",
            "desktop/notification_model.py",
            "shop/controller.py",
        ):
            with self.subTest(path=relative_path):
                source = (ROOT / relative_path).read_text(encoding="utf-8")
                self.assertIn("SettingsStore()", source)
                self.assertIn("palette_for_settings(self.settings)", source)

    def test_mode_selector_recolors_both_emblems_and_intro_video(self):
        source = (ROOT / "launcher/qml/ModeSelector.qml").read_text(encoding="utf-8")
        self.assertEqual(source.count("recolor.frag.qsb"), 3)
        self.assertIn("desktop-logo-alpha.png", source)
        self.assertIn("gaming-logo-alpha.png", source)
        self.assertIn("property color accentA: window.accentPrimary", source)
        self.assertIn("property color accentB: window.accentSecondary", source)

    def test_gaming_recolors_header_emblem_and_return_video(self):
        source = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertEqual(source.count("recolor.frag.qsb"), 2)
        self.assertIn("gaming-logo-alpha.png", source)
        self.assertIn("property color accentA: window.accentPrimary", source)
        self.assertIn("property color accentB: window.accentSecondary", source)

    def test_builds_the_qt_shader_before_qml_lint_and_image_packaging(self):
        script = (ROOT / "tools/compile-theme-shader.sh").read_text(encoding="utf-8")
        for workflow in (".github/workflows/build.yml", ".github/workflows/recipe-checks.yml"):
            source = (ROOT / workflow).read_text(encoding="utf-8")
            self.assertIn("qt6-qtshadertools-devel", source)
            self.assertIn("bash tools/compile-theme-shader.sh", source)
        self.assertIn("qsb-qt6 -o", script)
        self.assertIn("branding/shaders/recolor.frag.qsb", script)


if __name__ == "__main__":
    unittest.main()
