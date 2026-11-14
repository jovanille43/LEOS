"""Tests for pure LEOS game-library category filtering."""

import unittest

from pathlib import Path
import tempfile

from gaming.backend.library_state import (
    filter_games, read_bounded_json, validate_manual_game_input,
    MAX_MANUAL_ARGUMENTS, MAX_MANUAL_ARGUMENT_LENGTH, MAX_MANUAL_COMMAND_LENGTH,
    MAX_MANUAL_PLATFORM_LENGTH, MAX_MANUAL_TITLE_LENGTH,
)


class LibraryStateTests(unittest.TestCase):
    def setUp(self):
        self.games = [
            {"id": "steam:1", "title": "Alpha", "platform": "PC", "app_id": "440", "source": "Steam"},
            {"id": "manual:zelda", "title": "Zelda", "platform": "Nintendo"},
            {"id": "manual:ps", "title": "Racer", "platform": "PlayStation"},
            {"id": "manual:arcade", "title": "Arcade", "platform": "Arcade"},
            {"id": "manual:sega", "title": "Sonic", "platform": "SEGA"},
        ]

    def test_bounded_json_writer_sets_private_permissions(self):
        import os
        from gaming.backend.library_state import write_bounded_json

        if os.name != "posix":
            self.skipTest("POSIX permissions unavailable")
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory) / "state"
            parent.mkdir(mode=0o755)
            parent.chmod(0o755)
            path = parent / "favorites.json"
            write_bounded_json(path, ["steam:1", "heroic:two"])
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(parent.stat().st_mode & 0o777, 0o700)
            self.assertEqual(read_bounded_json(path), ["steam:1", "heroic:two"])

    def test_bounded_json_writer_rejects_oversize_without_replacing_file(self):
        from gaming.backend.library_state import write_bounded_json

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            write_bounded_json(path, {"keep": True})
            original = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "storage limit"):
                write_bounded_json(path, {"payload": "x" * 100}, max_bytes=16)
            self.assertEqual(path.read_bytes(), original)

    def test_bounded_json_writer_rejects_symbolic_links(self):
        from gaming.backend.library_state import write_bounded_json

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.json"
            target.write_text('{"keep":true}', encoding="utf-8")
            link = root / "state.json"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("Symbolic links unavailable")
            with self.assertRaises(OSError):
                write_bounded_json(link, {"replace": True})
            self.assertEqual(target.read_text(encoding="utf-8"), '{"keep":true}')
            self.assertTrue(link.is_symlink())

    def test_bounded_text_reader_rejects_oversized_metadata(self):
        from gaming.backend.library_state import read_bounded_text

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "libraryfolders.vdf"
            path.write_text('"path" "/games"', encoding="utf-8")
            self.assertIn("/games", read_bounded_text(path))
            self.assertIsNone(read_bounded_text(path, max_bytes=2))
            self.assertIsNone(read_bounded_text(path.with_name("missing.vdf")))

    def test_bounded_readers_reject_invalid_limits_and_symbolic_links(self):
        from gaming.backend.library_state import read_bounded_text

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.json"
            target.write_text('{"keep":true}', encoding="utf-8")
            link = root / "linked.json"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("Symbolic links unavailable")
            self.assertIsNone(read_bounded_json(link))
            self.assertIsNone(read_bounded_text(link))
            self.assertIsNone(read_bounded_json(target, max_bytes=-1))
            self.assertIsNone(read_bounded_text(target, max_bytes=-1))
            self.assertEqual(target.read_text(encoding="utf-8"), '{"keep":true}')

    def test_bounded_json_reader_accepts_valid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text('["steam:1"]', encoding="utf-8")
            self.assertEqual(read_bounded_json(path), ["steam:1"])

    def test_bounded_json_reader_rejects_oversized_and_malformed_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_bytes(b"12345")
            self.assertIsNone(read_bounded_json(path, max_bytes=4))
            path.write_text("{broken", encoding="utf-8")
            self.assertIsNone(read_bounded_json(path))
            self.assertIsNone(read_bounded_json(path.with_name("missing.json")))

    def test_bounded_json_reader_rejects_deeply_nested_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text("[" * 2000 + "0" + "]" * 2000, encoding="utf-8")
            self.assertIsNone(read_bounded_json(path))

    def test_manual_game_validation_accepts_safe_argument_lists(self):
        result = validate_manual_game_input(
            "  Mon jeu  préféré  ", " PC ", '"/opt/games/my game" --fullscreen'
        )
        self.assertEqual(
            result,
            ("Mon jeu préféré", "PC", ["/opt/games/my game", "--fullscreen"]),
        )

    def test_manual_game_validation_rejects_oversized_and_malformed_input(self):
        invalid = [
            (None, "PC", "game"),
            ("", "PC", "game"),
            ("x" * (MAX_MANUAL_TITLE_LENGTH + 1), "PC", "game"),
            ("Game", "P" * (MAX_MANUAL_PLATFORM_LENGTH + 1), "game"),
            ("Game", "PC", "x" * (MAX_MANUAL_COMMAND_LENGTH + 1)),
            ("Game", "PC", '"unterminated'),
            ("Game", "PC", "game " + " ".join(f"arg{i}" for i in range(MAX_MANUAL_ARGUMENTS))),
            ("Game", "PC", "game " + "x" * (MAX_MANUAL_ARGUMENT_LENGTH + 1)),
            ("Game", "PC", "game\x00bad"),
        ]
        for values in invalid:
            with self.subTest(values=values):
                self.assertIsNone(validate_manual_game_input(*values))

    def test_manual_game_validation_does_not_invoke_a_shell(self):
        result = validate_manual_game_input("Game", "PC", "game; rm -rf /")
        self.assertEqual(result, ("Game", "PC", ["game;", "rm", "-rf", "/"]))

    def test_home_returns_all_games(self):
        self.assertEqual(len(filter_games(self.games, "Accueil", set(), [])), 5)

    def test_platform_categories_filter_correctly(self):
        self.assertEqual(
            [item["id"] for item in filter_games(self.games, "Nintendo", set(), [])],
            ["manual:zelda"],
        )
        self.assertEqual(
            [item["id"] for item in filter_games(self.games, "PC Gaming", set(), [])],
            ["steam:1"],
        )

    def test_emulation_category_includes_retroarch_playlists_only(self):
        games = [
            {"id": "retroarch:1", "title": "Metroid", "platform": "Nintendo", "source": "RetroArch"},
            {"id": "steam:1", "title": "Metroidvania", "platform": "PC", "source": "Steam"},
            {"id": "manual:emu", "title": "Arcade title", "platform": "Émulation", "source": "Ajout manuel"},
            {"id": "emulator:local", "title": "Local PS2", "platform": "PlayStation", "source": "Fichiers locaux"},
        ]
        result = filter_games(games, "Émulation", set(), [])
        self.assertEqual([game["id"] for game in result], ["retroarch:1", "manual:emu", "emulator:local"])

    def test_favorites_filter_by_game_identifier(self):
        result = filter_games(self.games, "Favoris", {"steam:1", "manual:sega"}, [])
        self.assertEqual([item["id"] for item in result], ["steam:1", "manual:sega"])

    def test_recent_games_follow_most_recent_order(self):
        result = filter_games(
            self.games, "Récemment joués", set(), ["manual:sega", "steam:1"]
        )
        self.assertEqual([item["id"] for item in result], ["manual:sega", "steam:1"])

    def test_search_matches_title_platform_and_source_case_insensitively(self):
        self.assertEqual(
            [game["id"] for game in filter_games(
                self.games, "Accueil", set(), [], "SONIC"
            )],
            ["manual:sega"],
        )
        self.assertEqual(
            [game["id"] for game in filter_games(
                self.games, "PC Gaming", set(), [], "pc"
            )],
            ["steam:1"],
        )
        self.assertEqual(
            [game["id"] for game in filter_games(
                self.games, "Accueil", set(), [], "playstation"
            )],
            ["manual:ps"],
        )

    def test_search_matches_steam_app_id_and_stable_provider_id(self):
        by_app_id = filter_games(self.games, "Accueil", set(), [], "440")
        self.assertEqual([game["id"] for game in by_app_id], ["steam:1"])

        by_provider_id = filter_games(self.games, "Accueil", set(), [], "steam:1")
        self.assertEqual([game["id"] for game in by_provider_id], ["steam:1"])

    def test_search_is_applied_after_category_filtering(self):
        result = filter_games(
            self.games, "Nintendo", set(), [], "racer"
        )
        self.assertEqual(result, [])

    def test_unknown_category_falls_back_to_all_games(self):
        self.assertEqual(len(filter_games(self.games, "Unknown", set(), [])), 5)


if __name__ == "__main__":
    unittest.main()
