"""First-run identity and session-entry regression tests."""

import ast
from pathlib import Path
import unittest

from desktop.branding_assets import source_asset_urls, only_recolored_asset_urls
from desktop.themes import DEFAULT_COLOR_A, DEFAULT_COLOR_B, SOURCE_COLOR_A, SOURCE_COLOR_B


ROOT = Path(__file__).resolve().parents[1]
SELECTOR = ROOT / "launcher" / "qml" / "ModeSelector.qml"


class FirstRunIdentityContractTests(unittest.TestCase):
    def test_unconfigured_preview_is_neutral_and_not_the_artwork_palette(self):
        self.assertNotEqual(DEFAULT_COLOR_A, SOURCE_COLOR_A)
        self.assertNotEqual(DEFAULT_COLOR_B, SOURCE_COLOR_B)
        for color in (DEFAULT_COLOR_A, DEFAULT_COLOR_B):
            self.assertEqual(color[1:3], color[3:5])
            self.assertEqual(color[3:5], color[5:7])

    def test_desktop_and_gaming_require_the_explicit_identity_choice(self):
        qml = SELECTOR.read_text(encoding="utf-8")
        self.assertIn("if (!leosTheme.themeColorsConfigured)", qml)
        self.assertIn("function requestGamingMode()", qml)
        self.assertIn("function requestDesktopMode()", qml)
        self.assertIn("identityDialog.open()", qml)
        self.assertIn("closePolicy: Popup.NoAutoClose", qml)
        self.assertIn("function applyIdentityColors()", qml)
        self.assertIn("VALIDER L'IDENTITÉ LEOS", qml)
        self.assertIn("onClicked: window.requestGamingMode()", qml)
        self.assertNotIn("Bazzite KDE", qml)
        self.assertNotIn("#102b3a", qml)
        self.assertNotIn("#321437", qml)

    def test_autostart_entry_is_packaged_in_the_system_image(self):
        entry = (ROOT / "desktop" / "autostart" / "leos-session.desktop").read_text(encoding="utf-8")
        recipe = (ROOT / "recipes" / "common-modules.yml").read_text(encoding="utf-8")
        wrapper = (ROOT / "packaging" / "leos-session-selector").read_text(encoding="utf-8")
        self.assertIn("Exec=/usr/bin/bash /usr/libexec/leos-session-selector", entry)
        self.assertIn("session-selector.log", wrapper)
        self.assertIn("/usr/share/leos/launcher/main.py", wrapper)
        self.assertIn("src: desktop/autostart/leos-session.desktop", recipe)
        self.assertIn("src: packaging/leos-session-selector", recipe)
        self.assertIn("dest: /usr/etc/xdg/autostart/", recipe)

    def test_selector_reports_qml_readiness_only_after_the_window_loads(self):
        main = (ROOT / "launcher" / "main.py").read_text(encoding="utf-8")
        root_check = main.index("if not engine.rootObjects():")
        ready_marker = main.index('print("LEOS mode selector QML loaded successfully", flush=True)')
        event_loop = main.index("exit_code = app.exec()")
        self.assertLess(root_check, ready_marker)
        self.assertLess(ready_marker, event_loop)

    def test_unconfigured_theme_defers_recoloring_until_user_selects_colors(self):
        controller = ROOT / "desktop" / "theme_controller.py"
        tree = ast.parse(controller.read_text(encoding="utf-8"))
        theme_class = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "ThemeController"
        )
        methods = {
            node.name: node
            for node in theme_class.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

        start_source = ast.get_source_segment(
            controller.read_text(encoding="utf-8"),
            methods["_start_asset_generation"],
        )
        refresh_source = ast.get_source_segment(
            controller.read_text(encoding="utf-8"),
            methods["refresh"],
        )
        self.assertIn("not self._colors_configured", start_source)
        self.assertIn("if self._colors_configured", refresh_source)
        self.assertIn("self._asset_attempt_snapshot = None", refresh_source)
        self.assertIn("else {}", refresh_source)

    def test_theme_asset_worker_fallback_helper_is_imported(self):
        controller = ROOT / "desktop" / "theme_controller.py"
        tree = ast.parse(controller.read_text(encoding="utf-8"))
        imported_names = {
            alias.asname or alias.name
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
            and node.module == "desktop.branding_assets"
            for alias in node.names
        }
        calls_helper = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "source_asset_urls"
            for node in ast.walk(tree)
        )
        self.assertTrue(calls_helper)
        self.assertIn("source_asset_urls", imported_names)

    def test_source_asset_fallbacks_are_hidden_until_recolored(self):
        originals = source_asset_urls()
        supplied = dict(originals)
        supplied["gamingLogoUrl"] = "file:///home/user/.cache/leos/custom/gaming-logo.png"
        self.assertEqual(
            only_recolored_asset_urls(supplied),
            {"gamingLogoUrl": supplied["gamingLogoUrl"]},
        )


if __name__ == "__main__":
    unittest.main()
