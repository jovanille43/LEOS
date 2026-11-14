"""Tests for safe local emulation game discovery."""

import tempfile
import unittest
from pathlib import Path

from gaming.backend.emulation_discovery import (
    discover_emulated_games,
    default_scan_roots,
)


class EmulationDiscoveryTests(unittest.TestCase):
    def test_default_roots_are_confined_to_user_home(self):
        home = Path("/home/example")
        self.assertEqual(
            default_scan_roots(home),
            tuple(home / name for name in ("Games", "ROMs", "Roms", "Emulation")),
        )

    def test_discovers_supported_files_without_reading_or_executing_them(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Games"
            root.mkdir()
            (root / "Super Metroid.sfc").write_bytes(b"not inspected")
            (root / "Gran Turismo.chd").write_bytes(b"not inspected")
            (root / "Game.exe").write_bytes(b"not a game format")
            games = discover_emulated_games([root])
            self.assertEqual(
                [game["title"] for game in games],
                ["Gran Turismo", "Super Metroid"],
            )
            by_title = {game["title"]: game for game in games}
            self.assertEqual(by_title["Gran Turismo"]["platform"], "PlayStation")
            self.assertEqual(by_title["Super Metroid"]["platform"], "Nintendo")
            self.assertEqual(by_title["Gran Turismo"]["source"], "Fichiers locaux")
            self.assertTrue(by_title["Gran Turismo"]["id"].startswith("emulator:"))
            self.assertEqual(by_title["Gran Turismo"]["path"], str((root / "Gran Turismo.chd").resolve()))

    def test_skips_hidden_directories_and_symbolic_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Games"
            root.mkdir()
            hidden = root / ".hidden"
            hidden.mkdir()
            (hidden / "Hidden.iso").touch()
            outside = Path(directory) / "Outside.iso"
            outside.touch()
            try:
                (root / "linked.iso").symlink_to(outside)
                (root / "linked-dir").symlink_to(hidden, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Symbolic links unavailable")
            self.assertEqual(discover_emulated_games([root]), [])

    def test_does_not_follow_symlink_roots(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            actual = base / "actual"
            actual.mkdir()
            (actual / "Game.chd").touch()
            link = base / "linked"
            try:
                link.symlink_to(actual, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Symbolic links unavailable")
            self.assertEqual(discover_emulated_games([link]), [])

    def test_respects_file_and_depth_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Games"
            nested = root / "one" / "two"
            nested.mkdir(parents=True)
            (root / "A.chd").touch()
            (root / "B.chd").touch()
            (nested / "C.chd").touch()
            self.assertEqual(len(discover_emulated_games([root], max_files=1)), 1)
            self.assertEqual(len(discover_emulated_games([root], max_depth=1)), 2)

    def test_duplicate_roots_do_not_duplicate_games(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Games"
            root.mkdir()
            (root / "Game.chd").touch()
            self.assertEqual(len(discover_emulated_games([root, root])), 1)

    def test_rejects_invalid_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Game.chd").touch()
            self.assertEqual(discover_emulated_games([root], max_files=0), [])
            self.assertEqual(discover_emulated_games([root], max_depth=-1), [])
            self.assertEqual(discover_emulated_games([root], max_depth=9), [])


if __name__ == "__main__":
    unittest.main()
