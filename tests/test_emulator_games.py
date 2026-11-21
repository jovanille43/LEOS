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
        (self.root / "Switch Game.nsp").write_bytes(b"switch")
        (self.root / "Homebrew.nro").write_bytes(b"homebrew")

        dolphin = scan_emulator_folder(
            "gamecube_wii", self.root, launch_prefix=["/usr/bin/dolphin-emu"]
        )
        pcsx2 = scan_emulator_folder(
            "ps2", self.root, launch_prefix=["/usr/bin/pcsx2-qt"]
        )
        ppsspp = scan_emulator_folder(
            "psp", self.root, launch_prefix=["/usr/bin/PPSSPPQt"]
        )
        eden = scan_emulator_folder(
            "eden", self.root, launch_prefix=["/usr/bin/eden"]
        )
        dolphin_game = next(game for game in dolphin if game["title"] == "A Game")
        pcsx2_game = next(game for game in pcsx2 if game["title"] == "B Game")
        ppsspp_game = next(game for game in ppsspp if game["title"] == "C Game")
        eden_game = next(game for game in eden if game["title"] == "Switch Game")
        homebrew_game = next(game for game in eden if game["title"] == "Homebrew")

        self.assertEqual(dolphin_game["launch"], [
            "/usr/bin/dolphin-emu", "-e", str(self.root / "A Game.iso")
        ])
        self.assertEqual(pcsx2_game["launch"], [
            "/usr/bin/pcsx2-qt", "-fullscreen", "--", str(self.root / "B Game.chd")
        ])
        self.assertEqual(ppsspp_game["launch"], [
            "/usr/bin/PPSSPPQt", str(self.root / "C Game.pbp")
        ])
        self.assertEqual(eden_game["launch"], [
            "/usr/bin/eden", "-f", str(self.root / "Switch Game.nsp")
        ])
        self.assertEqual(homebrew_game["launch"], [
            "/usr/bin/eden", "-f", str(self.root / "Homebrew.nro")
        ])
        self.assertEqual(eden_game["platform"], "Nintendo Switch")
        for game in (dolphin_game, pcsx2_game, ppsspp_game, eden_game, homebrew_game):
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

    def test_extensions_match_upstream_supported_game_formats(self):
        self.assertEqual(PLATFORM_SPECS["gamecube_wii"]["extensions"], {
            ".iso", ".gcm", ".gcz", ".ciso", ".wbfs", ".wia", ".nfs", ".rvz"
        })
        self.assertEqual(PLATFORM_SPECS["ps2"]["extensions"], {
            ".bin", ".iso", ".cue", ".mdf", ".chd", ".cso", ".zso"
        })
        self.assertEqual(PLATFORM_SPECS["psp"]["extensions"], {
            ".iso", ".cso", ".chd", ".pbp"
        })
        self.assertEqual(PLATFORM_SPECS["melonds"]["extensions"], {".nds"})
        self.assertEqual(
            PLATFORM_SPECS["eden"]["extensions"],
            {".nsp", ".xci", ".nro", ".nso"},
        )
        self.assertNotIn(".nrg", PLATFORM_SPECS["ps2"]["extensions"])
        self.assertNotIn(".wad", PLATFORM_SPECS["gamecube_wii"]["extensions"])

    def test_melonds_uses_fullscreen_rom_argument(self):
        game = self.root / "Nintendo DS.nds"
        game.write_bytes(b"rom")
        command = build_emulator_launch_command(
            "melonds",
            game,
            self.root,
            which=lambda name: "/usr/bin/melonDS" if name == "melonDS" else None,
        )
        self.assertEqual(command, ["/usr/bin/melonDS", "-f", str(game.resolve())])

    def test_eden_uses_fullscreen_flag_and_single_game_path(self):
        game = self.root / "Switch Game.xci"
        game.write_bytes(b"switch")
        command = build_emulator_launch_command(
            "eden",
            game,
            self.root,
            which=lambda name: "/usr/bin/eden" if name == "eden" else None,
        )
        self.assertEqual(command, ["/usr/bin/eden", "-f", str(game.resolve())])

    def test_eden_flatpak_mounts_only_the_selected_games_folder_read_only(self):
        data_home = Path(self.temporary.name) / "data"
        deployment = (
            data_home / "flatpak/app" / "dev.eden_emu.eden"
            / "x86_64/stable/commit/files"
        )
        deployment.mkdir(parents=True)
        prefix = build_emulator_launch_prefix(
            "eden",
            self.root,
            which=lambda name: "/usr/bin/flatpak" if name == "flatpak" else None,
            data_home=data_home,
            system_flatpak_root=Path(self.temporary.name) / "system-apps",
        )
        self.assertEqual(prefix, [
            "/usr/bin/flatpak", "run",
            f"--filesystem={self.root}:ro",
            "dev.eden_emu.eden",
        ])

    def test_rpcs3_imports_only_validated_ps3_disc_layouts(self):
        title = self.root / "Gran Turismo"
        ps3_game = title / "PS3_GAME"
        usrdir = ps3_game / "USRDIR"
        usrdir.mkdir(parents=True)
        (ps3_game / "PARAM.SFO").write_bytes(b"param-sfo")
        eboot = usrdir / "EBOOT.BIN"
        eboot.write_bytes(b"self")

        games = scan_emulator_folder(
            "rpcs3", self.root, launch_prefix=["/usr/bin/rpcs3"]
        )
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]["title"], "Gran Turismo")
        self.assertEqual(games[0]["content_path"], str(eboot))
        self.assertEqual(games[0]["launch"], [
            "/usr/bin/rpcs3", "--no-gui", "--fullscreen", str(eboot)
        ])
        self.assertEqual(games[0]["platform"], "PlayStation")

    def test_rpcs3_imports_psn_title_layout_and_supports_selecting_title_root(self):
        title = self.root / "NPUB12345"
        usrdir = title / "USRDIR"
        usrdir.mkdir(parents=True)
        (title / "PARAM.SFO").write_bytes(b"param-sfo")
        eboot = usrdir / "EBOOT.BIN"
        eboot.write_bytes(b"self")

        games = scan_emulator_folder(
            "rpcs3", title, launch_prefix=["/usr/bin/rpcs3"]
        )
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]["title"], "NPUB12345")
        self.assertEqual(games[0]["selected_root"], str(title.resolve()))

    def test_rpcs3_ignores_pkg_arbitrary_bins_and_unvalidated_eboots(self):
        (self.root / "Install.pkg").write_bytes(b"pkg")
        (self.root / "not-a-game.bin").write_bytes(b"bin")
        invalid = self.root / "Invalid" / "USRDIR"
        invalid.mkdir(parents=True)
        (invalid / "EBOOT.BIN").write_bytes(b"self")

        games = scan_emulator_folder(
            "rpcs3", self.root, launch_prefix=["/usr/bin/rpcs3"]
        )
        self.assertEqual(games, [])

    def test_rpcs3_flatpak_mounts_only_the_selected_games_root_read_only(self):
        data_home = Path(self.temporary.name) / "data"
        deployment = (
            data_home / "flatpak/app" / "net.rpcs3.RPCS3"
            / "x86_64/stable/commit/files"
        )
        deployment.mkdir(parents=True)
        prefix = build_emulator_launch_prefix(
            "rpcs3",
            self.root,
            which=lambda name: "/usr/bin/flatpak" if name == "flatpak" else None,
            data_home=data_home,
            system_flatpak_root=Path(self.temporary.name) / "system-apps",
        )
        self.assertEqual(prefix, [
            "/usr/bin/flatpak", "run",
            f"--filesystem={self.root}:ro",
            "net.rpcs3.RPCS3",
        ])

    def test_rpcs3_launch_revalidates_eboot_and_param_sfo_before_start(self):
        title = self.root / "Title"
        ps3_game = title / "PS3_GAME"
        usrdir = ps3_game / "USRDIR"
        usrdir.mkdir(parents=True)
        metadata = ps3_game / "PARAM.SFO"
        metadata.write_bytes(b"param-sfo")
        eboot = usrdir / "EBOOT.BIN"
        eboot.write_bytes(b"self")

        command = build_emulator_launch_command(
            "rpcs3", eboot, self.root,
            which=lambda name: "/usr/bin/rpcs3" if name == "rpcs3" else None,
        )
        self.assertEqual(command, [
            "/usr/bin/rpcs3", "--no-gui", "--fullscreen", str(eboot.resolve())
        ])

        metadata.unlink()
        self.assertEqual(
            build_emulator_launch_command(
                "rpcs3", eboot, self.root,
                which=lambda name: "/usr/bin/rpcs3" if name == "rpcs3" else None,
            ),
            [],
        )

    def test_rpcs3_refuses_symbolic_links_inside_the_selected_game_layout(self):
        title = self.root / "Title"
        ps3_game = title / "PS3_GAME"
        usrdir = ps3_game / "USRDIR"
        usrdir.mkdir(parents=True)
        (ps3_game / "PARAM.SFO").write_bytes(b"param-sfo")
        outside = Path(self.temporary.name) / "outside"
        outside.write_bytes(b"self")
        try:
            (usrdir / "EBOOT.BIN").symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolic links unavailable")
        self.assertEqual(
            scan_emulator_folder("rpcs3", self.root, launch_prefix=["rpcs3"]),
            [],
        )

    def test_supported_platforms_are_deliberately_limited_to_confirmed_cli_paths(self):
        self.assertEqual(
            set(PLATFORM_SPECS),
            {"gamecube_wii", "ps2", "psp", "melonds", "eden", "rpcs3"},
        )
        self.assertEqual(PLATFORM_SPECS["rpcs3"]["extensions"], frozenset())


if __name__ == "__main__":
    unittest.main()
