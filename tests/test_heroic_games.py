"""Tests for importing installed games from Heroic manifests."""

import json
import tempfile
import unittest
from pathlib import Path

from gaming.backend.heroic import find_heroic_artwork, load_heroic_games
from gaming.backend.install_state import installation_status


class HeroicGameImportTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.game_dir = self.root / "Installed Game"
        self.game_dir.mkdir()
        self.manifest = self.root / "installed.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_manifest(self, payload):
        self.manifest.write_text(json.dumps(payload), encoding="utf-8")

    def test_imports_epic_game_and_uses_heroic_protocol(self):
        self.write_manifest({
            "APP_NAME_123": {
                "app_name": "APP_NAME_123",
                "title": "Example Epic Game",
                "install_path": str(self.game_dir),
            }
        })
        games = load_heroic_games(self.manifest, "legendary")
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]["title"], "Example Epic Game")
        self.assertEqual(games[0]["source"], "Epic Games · Heroic")
        self.assertEqual(
            games[0]["launch"][0],
            "heroic://launch?appName=APP_NAME_123&runner=legendary&gui=false",
        )

    def test_keeps_missing_install_paths_and_skips_dlc(self):
        missing = self.root / "not-installed"
        self.write_manifest({
            "BASE": {
                "app_name": "BASE",
                "title": "Base game",
                "install_path": str(self.game_dir),
            },
            "DLC": {
                "app_name": "DLC",
                "title": "Extra content",
                "install_path": str(self.game_dir),
                "is_dlc": True,
            },
            "MISSING": {
                "app_name": "MISSING",
                "title": "Missing game",
                "install_path": str(missing),
            },
        })
        games = load_heroic_games(self.manifest, "legendary")
        self.assertEqual([game["app_id"] for game in games], ["BASE", "MISSING"])
        self.assertEqual(installation_status(games[0]), "Installé")
        self.assertEqual(installation_status(games[1]), "Fichiers absents")

    def test_supports_gog_runner_and_url_encodes_identifier(self):
        self.write_manifest([{
            "appName": "my game 42",
            "appTitle": "My GOG Game",
            "installPath": str(self.game_dir),
        }])
        games = load_heroic_games(self.manifest, "gog")
        self.assertEqual(len(games), 1)
        self.assertIn("appName=my%20game%2042", games[0]["launch"][0])
        self.assertIn("runner=gog", games[0]["launch"][0])

    def test_imports_existing_local_cover_artwork(self):
        artwork = self.root / "cover.webp"
        artwork.write_bytes(b"image")
        self.write_manifest({
            "APP": {
                "app_name": "APP",
                "title": "Covered Game",
                "install_path": str(self.game_dir),
                "art_cover": str(artwork),
            }
        })
        games = load_heroic_games(self.manifest, "legendary")
        self.assertEqual(games[0]["artwork"], artwork.resolve().as_uri())

    def test_ignores_remote_urls_and_unsupported_artwork_files(self):
        self.assertEqual(
            find_heroic_artwork({"art_cover": "https://example.invalid/cover.jpg"}),
            "",
        )
        unsupported = self.root / "cover.svg"
        unsupported.write_text("<svg/>", encoding="utf-8")
        self.assertEqual(find_heroic_artwork({"icon": str(unsupported)}), "")

    def test_rejects_unsupported_runner_and_corrupt_files(self):
        self.write_manifest({})
        self.assertEqual(load_heroic_games(self.manifest, "other"), [])
        self.manifest.write_text("{broken", encoding="utf-8")
        self.assertEqual(load_heroic_games(self.manifest, "legendary"), [])


if __name__ == "__main__":
    unittest.main()
