"""Tests for read-only Lutris SQLite library import."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from gaming.backend.lutris import find_lutris_artwork, load_lutris_games


class LutrisImportTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_dir.name) / "pga.db"
        connection = sqlite3.connect(self.database)
        connection.execute(
            """
            CREATE TABLE games (
                id INTEGER PRIMARY KEY,
                name TEXT,
                slug TEXT,
                runner TEXT,
                installed INTEGER,
                directory TEXT,
                executable TEXT,
                platform TEXT,
                service TEXT
            )
            """
        )
        connection.executemany(
            """
            INSERT INTO games
            (id, name, slug, runner, installed, directory, executable, platform, service)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (12, "Installed Wine Game", "installed-wine-game", "wine", 1, "/games/a", "game.exe", "windows", None),
                (13, "Native Linux Game", "native-linux-game", "linux", 1, "/games/b", "run.sh", "linux", None),
                (14, "Not Installed", "not-installed", "wine", 0, "/games/c", "game.exe", "windows", None),
                (15, "", "invalid", "wine", 1, "/games/d", "game.exe", "windows", None),
            ],
        )
        connection.commit()
        connection.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_imports_only_valid_installed_games(self):
        games = load_lutris_games(self.database)
        self.assertEqual([game["app_id"] for game in games], ["12", "13"])
        self.assertEqual(games[0]["source"], "Lutris · wine")
        self.assertEqual(games[1]["title"], "Native Linux Game")

    def test_import_is_bounded_to_configured_game_limit(self):
        from unittest.mock import patch

        with patch("gaming.backend.lutris.MAX_LUTRIS_GAMES", 1):
            games = load_lutris_games(self.database)
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]["app_id"], "12")

    def test_launch_uses_lutris_numeric_game_identifier(self):
        games = load_lutris_games(self.database)
        self.assertEqual(games[0]["launch"], ["lutris:rungameid/12"])

    def test_rejects_non_numeric_or_non_positive_catalog_ids(self):
        database = Path(self.temp_dir.name) / "invalid-ids.db"
        connection = sqlite3.connect(database)
        connection.execute(
            "CREATE TABLE games (id TEXT, name TEXT, slug TEXT, runner TEXT, installed INTEGER)"
        )
        connection.executemany(
            "INSERT INTO games VALUES (?, ?, ?, ?, ?)",
            [
                ("not-a-number", "Invalid ID", "invalid-id", "wine", 1),
                ("0", "Zero ID", "zero-id", "wine", 1),
                ("-4", "Negative ID", "negative-id", "wine", 1),
                ("42", "Valid ID", "valid-id", "wine", 1),
            ],
        )
        connection.commit()
        connection.close()
        games = load_lutris_games(database)
        self.assertEqual([game["app_id"] for game in games], ["42"])
        self.assertEqual(games[0]["launch"], ["lutris:rungameid/42"])

    def test_finds_existing_local_cover_art(self):
        data_home = Path(self.temp_dir.name) / "data"
        cover_dir = data_home / "lutris" / "coverart"
        cover_dir.mkdir(parents=True)
        cover = cover_dir / "installed-wine-game.webp"
        cover.write_bytes(b"local-art")
        self.assertEqual(
            find_lutris_artwork(data_home, "installed-wine-game"),
            cover.resolve(),
        )

    def test_artwork_lookup_rejects_path_traversal_and_missing_files(self):
        data_home = Path(self.temp_dir.name) / "data"
        self.assertIsNone(find_lutris_artwork(data_home, "../secret"))
        self.assertIsNone(find_lutris_artwork(data_home, "unknown-game"))

    def test_import_is_read_only(self):
        before = self.database.read_bytes()
        load_lutris_games(self.database)
        self.assertEqual(self.database.read_bytes(), before)

    def test_missing_or_invalid_database_returns_empty_list(self):
        self.assertEqual(load_lutris_games(self.database.parent / "missing.db"), [])
        invalid = self.database.parent / "invalid.db"
        invalid.write_text("not a database", encoding="utf-8")
        self.assertEqual(load_lutris_games(invalid), [])


if __name__ == "__main__":
    unittest.main()
