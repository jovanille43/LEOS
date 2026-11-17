"""Integration contract for launching local games from Gaming Mode."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class GamingEmulatorLaunchIntegrationTests(unittest.TestCase):
    def test_library_routes_local_files_through_the_safe_emulator_resolver(self):
        source = (ROOT / "gaming/backend/library.py").read_text(encoding="utf-8")
        self.assertIn("from .emulator_launch import build_emulator_launch_command", source)
        self.assertIn('game.get("source") == "Fichiers locaux"', source)
        self.assertIn("build_emulator_launch_command(game.get(\"path\", \"\"))", source)
        self.assertIn("process.setProgram(emulator_command[0])", source)
        self.assertIn("process.setArguments(emulator_command[1:])", source)

    def test_qml_exposes_a_user_confirmed_launch_action_for_local_files(self):
        qml = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("enabled: window.selectedIndex >= 0", qml)
        self.assertIn('"OUVRIR AVEC UN ÉMULATEUR"', qml)
        library = (ROOT / "gaming/backend/library.py").read_text(encoding="utf-8")
        self.assertIn("émulateur selon format et installation", library)

    def test_flatpak_file_forwarding_is_used_without_shell_execution(self):
        source = (ROOT / "gaming/backend/emulator_launch.py").read_text(encoding="utf-8")
        self.assertIn('"--file-forwarding"', source)
        self.assertIn('"@@"', source)
        self.assertNotIn("subprocess", source)
        self.assertNotIn("shell=True", source)

    def test_emulator_catalog_ids_match_launch_resolver(self):
        import json

        catalog = json.loads((ROOT / "shop/catalog.json").read_text(encoding="utf-8"))
        ids = {entry.get("id") for entry in catalog}
        source = (ROOT / "gaming/backend/emulator_launch.py").read_text(encoding="utf-8")
        for app_id in (
            "org.DolphinEmu.dolphin-emu",
            "info.cemu.Cemu",
            "dev.eden_emu.eden",
            "org.ppsspp.PPSSPP",
        ):
            with self.subTest(app_id=app_id):
                self.assertIn(app_id, ids)
                self.assertIn(app_id, source)


if __name__ == "__main__":
    unittest.main()
