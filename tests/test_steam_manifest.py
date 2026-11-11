"""Tests for safe Steam manifest metadata parsing."""

import tempfile
import unittest
from pathlib import Path

from gaming.backend.library import GameLibraryModel


class SteamManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.steamapps = self.root / "steamapps"
        self.steamapps.mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def read_manifest(self, installdir):
        manifest = self.steamapps / "appmanifest_123.acf"
        manifest.write_text(
            '"AppState" {\n'
            '    "appid" "123"\n'
            '    "name" "Example Game"\n'
            f'    "installdir" "{installdir}"\n'
            '}\n',
            encoding="utf-8",
        )
        return GameLibraryModel._read_steam_manifest(manifest)

    def test_reads_safe_install_directory(self):
        game = self.read_manifest("Example Game")
        self.assertEqual(game["app_id"], "123")
        self.assertEqual(
            game["install_path"],
            str(self.steamapps / "common" / "Example Game"),
        )

    def test_rejects_parent_and_nested_install_paths(self):
        for value in ("..", ".", "../outside", "nested/game", r"nested\\game"):
            with self.subTest(value=value):
                game = self.read_manifest(value)
                self.assertEqual(game["install_path"], "")


if __name__ == "__main__":
    unittest.main()
