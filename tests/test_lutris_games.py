"""Tests for read-only Lutris SQLite library import."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from gaming.backend.lutris import load_lutris_games


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

    def test_launch_uses_lutris_numeric_game_identifier(self):
        games = load_lutris_games(self.database)
        self.assertEqual(games[0]["launch"], ["lutris:rungameid/12"])

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
