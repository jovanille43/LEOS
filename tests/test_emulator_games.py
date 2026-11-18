"""Tests for explicit, bounded and read-only console game folder scans."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gaming.backend.emulator_games import (
    PLATFORM_SPECS,
    build_emulator_launch_command,
    build_emulator_launch_prefix,
    scan_emulator_folder,
)


class EmulatorGameFolderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "games"
        self.root.mkdir()
        self.nested = self.root / "Collection" / "Disc 1"
        self.nested.mkdir(parents=True)

    def tearDown(self):
        self.temporary.cleanup()

    def test_only_imports_supported_files_from_selected_platform(self):
        (self.root / "Mario Kart.iso").write_bytes(b"disc")
        (self.nested / "The Legend of Zelda.rvz").write_bytes(b"disc")
        (self.root / "not-a-game.txt").write_text("ignored", encoding="utf-8")
        (self.root / "PSP game.cso").write_bytes(b"ignored")

        games = scan_emulator_folder(
            "gamecube_wii", self.root, launch_prefix=["/usr/bin/dolphin-emu"]
        )
        self.assertEqual({game["title"] for game in games}, {
            "Mario Kart", "The Legend of Zelda"
        })
        self.assertTrue(all(game["platform"] == "Nintendo" for game in games))
        self.assertTrue(all(game["source"] == "Dolphin" for game in games))

    def test_builds_documented_argument_arrays_without_a_shell(self):
        (self.root / "A Game.iso").write_bytes(b"disc")
        (self.root / "B Game.chd").write_bytes(b"disc")
        (self.root / "C Game.pbp").write_bytes(b"disc")

        dolphin = scan_emulator_folder(
            "gamecube_wii", self.root, launch_prefix=["/usr/bin/dolphin-emu"]
        )
        pcsx2 = scan_emulator_folder(
            "ps2", self.root, launch_prefix=["/usr/bin/pcsx2-qt"]
        )
        ppsspp = scan_emulator_folder(
            "psp", self.root, launch_prefix=["/usr/bin/PPSSPPQt"]
        )
        dolphin_game = next(game for game in dolphin if game["title"] == "A Game")
        pcsx2_game = next(game for game in pcsx2 if game["title"] == "B Game")
        ppsspp_game = next(game for game in ppsspp if game["title"] == "C Game")

        self.assertEqual(dolphin_game["launch"], [
            "/usr/bin/dolphin-emu", "-e", str(self.root / "A Game.iso")
        ])
        self.assertEqual(pcsx2_game["launch"], [
            "/usr/bin/pcsx2-qt", "-fullscreen", "--", str(self.root / "B Game.chd")
        ])
        self.assertEqual(ppsspp_game["launch"], [
            "/usr/bin/PPSSPPQt", str(self.root / "C Game.pbp")
        ])
        for game in (dolphin_game, pcsx2_game, ppsspp_game):
            self.assertTrue(all(isinstance(part, str) for part in game["launch"]))
            self.assertIn("content_path", game)
            self.assertIn("selected_root", game)

    def test_skips_hidden_files_and_symbolic_links(self):
        (self.root / "Visible.iso").write_bytes(b"disc")
        (self.root / ".hidden.iso").write_bytes(b"disc")
        outside = Path(self.temporary.name) / "outside.iso"
        outside.write_bytes(b"private")
        try:
            (self.root / "linked.iso").symlink_to(outside)
            (self.root / "linked-folder").symlink_to(self.nested, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolic links unavailable")
        (self.nested / "Nested.iso").write_bytes(b"disc")

        games = scan_emulator_folder(
            "gamecube_wii", self.root, launch_prefix=["dolphin-emu"]
        )
        names = {game["title"] for game in games}
        self.assertEqual(names, {"Visible", "Nested"})
        self.assertNotIn("linked", names)
        self.assertNotIn(".hidden", names)

    def test_rejects_invalid_platforms_and_symlinked_selected_roots(self):
        self.assertEqual(
            scan_emulator_folder("unknown", self.root, launch_prefix=["emu"]),
            [],
        )
        linked = Path(self.temporary.name) / "linked-root"
        try:
            linked.symlink_to(self.root, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolic links unavailable")
        self.assertEqual(
            scan_emulator_folder("ps2", linked, launch_prefix=["pcsx2"]),
            [],
        )

    def test_enforces_scan_depth_and_entry_limits(self):
        (self.root / "Root.iso").write_bytes(b"disc")
        (self.nested / "Deep.iso").write_bytes(b"disc")
        with patch("gaming.backend.emulator_games.MAX_SCAN_DEPTH", 0):
            games = scan_emulator_folder(
                "gamecube_wii", self.root, launch_prefix=["dolphin"]
            )
        self.assertEqual([game["title"] for game in games], ["Root"])

        with patch("gaming.backend.emulator_games.MAX_SCAN_ENTRIES", 1):
            limited = scan_emulator_folder(
                "gamecube_wii", self.root, launch_prefix=["dolphin"]
            )
        self.assertLessEqual(len(limited), 1)

    def test_detects_native_emulator_before_flatpak(self):
        found = build_emulator_launch_prefix(
            "gamecube_wii",
            self.root,
            which=lambda name: "/usr/bin/dolphin-emu" if name == "dolphin-emu" else None,
            data_home=Path(self.temporary.name) / "data",
            system_flatpak_root=Path(self.temporary.name) / "system-apps",
        )
        self.assertEqual(found, ["/usr/bin/dolphin-emu"])

    def test_builds_flatpak_launch_with_only_selected_folder_read_only(self):
        data_home = Path(self.temporary.name) / "data"
        deployment = (
            data_home / "flatpak/app" / "org.ppsspp.PPSSPP"
            / "x86_64/stable/commit/files"
        )
        deployment.mkdir(parents=True)
        found = build_emulator_launch_prefix(
            "psp",
            self.root,
            which=lambda name: "/usr/bin/flatpak" if name == "flatpak" else None,
            data_home=data_home,
            system_flatpak_root=Path(self.temporary.name) / "system-apps",
        )
        self.assertEqual(found, [
            "/usr/bin/flatpak", "run",
            f"--filesystem={self.root}:ro",
            "org.ppsspp.PPSSPP",
        ])

    def test_rebuilds_launch_command_and_rejects_files_outside_chosen_root(self):
        game = self.root / "Title.iso"
        game.write_bytes(b"disc")
        command = build_emulator_launch_command(
            "gamecube_wii", game, self.root,
            which=lambda name: "/usr/bin/dolphin-emu" if name == "dolphin-emu" else None,
        )
        self.assertEqual(command, ["/usr/bin/dolphin-emu", "-e", str(game.resolve())])

        outside = Path(self.temporary.name) / "outside.iso"
        outside.write_bytes(b"disc")
        self.assertEqual(
            build_emulator_launch_command(
                "gamecube_wii", outside, self.root,
                which=lambda name: "/usr/bin/dolphin-emu" if name == "dolphin-emu" else None,
            ),
            [],
        )

    def test_no_game_is_imported_without_an_installed_emulator(self):
        (self.root / "Game.iso").write_bytes(b"disc")
        self.assertEqual(
            build_emulator_launch_prefix(
                "gamecube_wii",
                self.root,
                which=lambda _name: None,
                data_home=Path(self.temporary.name) / "data",
                system_flatpak_root=Path(self.temporary.name) / "system-apps",
            ),
            [],
        )
        self.assertEqual(
            scan_emulator_folder("gamecube_wii", self.root, launch_prefix=[]),
            [],
        )

    def test_supported_platforms_are_deliberately_limited_to_confirmed_cli_paths(self):
        self.assertEqual(set(PLATFORM_SPECS), {"gamecube_wii", "ps2", "psp"})


if __name__ == "__main__":
    unittest.main()
