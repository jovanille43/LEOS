"""Source-contract tests for the Gaming MangoHud controls."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MangoHudIntegrationTests(unittest.TestCase):
    def test_controller_exposes_persisted_optional_preference(self):
        source = (ROOT / "gaming/backend/controller.py").read_text(encoding="utf-8")
        self.assertIn("def mangoHudAvailable", source)
        self.assertIn("def mangoHudEnabled", source)
        self.assertIn('gaming_mangohud_enabled', source)
        self.assertIn("mango_hud=bool(mango_hud and self._mangohud_enabled)", source)

    def test_direct_launch_wrapper_is_used_without_shell(self):
        source = (ROOT / "gaming/backend/library.py").read_text(encoding="utf-8")
        self.assertIn("build_launch_command(launch_command, bool(mango_hud))", source)
        self.assertIn("process.setProgram(executable)", source)
        self.assertIn("process.setArguments(command[1:])", source)
        self.assertNotIn("shell=True", source)

    def test_quick_panel_explains_steam_manual_configuration(self):
        source = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn('text: "Overlay FPS · MangoHud"', source)
        self.assertIn("mangohud %command%", source)
        self.assertIn("leos.launchGame(window.selectedIndex, leos.mangoHudEnabled)", source)


if __name__ == "__main__":
    unittest.main()
