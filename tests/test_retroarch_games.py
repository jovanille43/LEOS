"""Tests for safe, read-only RetroArch playlist imports."""

import json
import tempfile
import unittest
from pathlib import Path

from gaming.backend.retroarch import (
    find_retroarch_playlist_directories,
    load_retroarch_games,
)
from gaming.backend.install_state import installation_status


class RetroArchPlaylistTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.playlists = self.root / "playlists"
        self.playlists.mkdir()
        self.roms = self.root / "ROMs"
        self.roms.mkdir()
        self.rom = self.roms / "Game.sfc"
        self.rom.write_bytes(b"rom")
        self.core = self.root / "cores" / "snes9x_libretro.so"
        self.core.parent.mkdir()
        self.core.write_bytes(b"core")
        self.playlist = self.playlists / "Nintendo - Super Nintendo.lpl"

    def tearDown(self):
        self.temporary.cleanup()

    def write_playlist(self, items, **extra):
        payload = {"version": "1.0", "items": items, **extra}
        self.playlist.write_text(json.dumps(payload), encoding="utf-8")

    def test_classifies_playstation_and_sega_playlist_databases(self):
        playstation = self.playlists / "Sony - PlayStation.lpl"
        playstation.write_text(json.dumps({"items": [{
            "path": str(self.rom), "label": "PlayStation Game",
            "db_name": "Sony - PlayStation.lpl",
        }]}), encoding="utf-8")
        sega = self.playlists / "Sega - Mega Drive.lpl"
        sega.write_text(json.dumps({"items": [{
            "path": str(self.rom), "label": "Sega Game",
            "db_name": "Sega - Mega Drive.lpl",
        }]}), encoding="utf-8")

        self.assertEqual(load_retroarch_games(playstation)[0]["platform"], "PlayStation")
        self.assertEqual(load_retroarch_games(sega)[0]["platform"], "SEGA")

    def test_discovers_xdg_flatpak_and_configured_playlist_directories(self):
        home = self.root / "home"
        home.mkdir()
        xdg = self.root / "xdg-config"
        native = home / ".config/retroarch"
        flatpak = home / ".var/app/org.libretro.RetroArch/config/retroarch"
        custom = self.root / "custom-playlists"
        for directory in (
            xdg / "retroarch/playlists",
            native / "playlists",
            flatpak / "playlists",
            custom,
        ):
            directory.mkdir(parents=True)

        (native / "retroarch.cfg").write_text(
            f'playlist_directory = "{custom}"\\n',
            encoding="utf-8",
        )
        found = find_retroarch_playlist_directories(home, xdg)

        self.assertIn((xdg / "retroarch/playlists").resolve(), found)
        self.assertIn((native / "playlists").resolve(), found)
        self.assertIn((flatpak / "playlists").resolve(), found)
        self.assertIn(custom.resolve(), found)

    def test_relative_xdg_config_home_falls_back_to_home_config(self):
        home = self.root / "home"
        default = home / ".config/retroarch/playlists"
        default.mkdir(parents=True)
        found = find_retroarch_playlist_directories(home, Path("relative-config"))
        self.assertIn(default.resolve(), found)

    def test_imports_nintendo_playlist_and_builds_native_core_command(self):
        self.write_playlist([{
            "path": str(self.rom),
            "label": "Super Mario World",
            "core_path": str(self.core),
            "core_name": "Snes9x",
            "db_name": "Nintendo - Super Nintendo.lpl",
        }])
        games = load_retroarch_games(
            self.playlist, native_executable="/usr/bin/retroarch"
        )
        self.assertEqual(len(games), 1)
        game = games[0]
        self.assertEqual(game["platform"], "Nintendo")
        self.assertEqual(game["title"], "Super Mario World")
        self.assertEqual(game["source"], "RetroArch · Snes9x")
        self.assertEqual(game["content_path"], str(self.rom))
        self.assertEqual(
            game["launch"],
            ["/usr/bin/retroarch", "-L", str(self.core), str(self.rom)],
        )
        self.assertEqual(installation_status(game), "Installé")

    def test_uses_playlist_default_core_when_item_core_is_detect(self):
        self.write_playlist([{
            "path": str(self.rom),
            "label": "Default Core Game",
            "core_path": "DETECT",
            "core_name": "DETECT",
        }], default_core_path=str(self.core), default_core_name="Snes9x")
        game = load_retroarch_games(self.playlist)[0]
        self.assertEqual(game["core_name"], "Snes9x")
        self.assertIn("-L", game["launch"])
        self.assertIn(str(self.core), game["launch"])

    def test_detect_core_falls_back_to_retroarch_core_selection(self):
        self.write_playlist([{
            "path": str(self.rom),
            "label": "Choose a Core",
            "core_path": "DETECT",
            "core_name": "DETECT",
        }])
        game = load_retroarch_games(self.playlist, native_executable="retroarch")[0]
        self.assertEqual(game["launch"], ["retroarch", str(self.rom)])

    def test_portable_relative_playlist_path_uses_declared_base_directory(self):
        self.write_playlist([{
            "path": "Game.sfc",
            "label": "Portable Game",
            "core_path": "DETECT",
        }], base_content_directory=str(self.roms))
        game = load_retroarch_games(self.playlist)[0]
        self.assertEqual(game["content_path"], str(self.rom))

    def test_flatpak_launch_grants_only_read_only_rom_directory_access(self):
        self.write_playlist([{
            "path": str(self.rom),
            "label": "Flatpak Game",
            "core_path": "DETECT",
        }])
        game = load_retroarch_games(
            self.playlist, native_executable=None, flatpak_available=True
        )[0]
        self.assertEqual(game["launch"][:4], [
            "flatpak", "run", f"--filesystem={self.roms}:ro",
            "org.libretro.RetroArch",
        ])
        self.assertEqual(game["launch"][-1], str(self.rom))

    def test_flatpak_runtime_core_is_not_passed_to_missing_native_launcher(self):
        self.write_playlist([{
            "path": str(self.rom),
            "label": "Flatpak Only Core",
            "core_path": "/app/lib/libretro/fake_libretro.so",
        }])
        game = load_retroarch_games(
            self.playlist, native_executable=None, flatpak_available=False
        )[0]
        self.assertEqual(game["launch"], ["retroarch", str(self.rom)])

    def test_flatpak_custom_core_gets_its_own_read_only_permission(self):
        self.write_playlist([{
            "path": str(self.rom),
            "label": "Flatpak Core Game",
            "core_path": str(self.core),
        }])
        game = load_retroarch_games(
            self.playlist, native_executable=None, flatpak_available=True
        )[0]
        self.assertIn(f"--filesystem={self.roms}:ro", game["launch"])
        self.assertIn(f"--filesystem={self.core.parent}:ro", game["launch"])
        self.assertIn("-L", game["launch"])
        self.assertIn(str(self.core), game["launch"])

    def test_archive_playlist_entry_checks_archive_file(self):
        archive = self.roms / "Arcade.zip"
        archive.write_bytes(b"zip")
        self.write_playlist([{
            "path": f"{archive}#AlienArena.rom",
            "label": "Alien Arena",
            "core_path": "DETECT",
            "db_name": "MAME 2003-Plus.lpl",
        }])
        game = load_retroarch_games(self.playlist)[0]
        self.assertEqual(game["platform"], "Arcade")
        self.assertEqual(installation_status(game), "Installé")

    def test_missing_rom_is_kept_and_reported_as_missing(self):
        missing = self.roms / "Missing.nes"
        self.write_playlist([{
            "path": str(missing),
            "label": "Missing ROM",
            "core_path": "DETECT",
            "db_name": "Nintendo - NES.lpl",
        }])
        game = load_retroarch_games(self.playlist)[0]
        self.assertEqual(game["platform"], "Nintendo")
        self.assertEqual(installation_status(game), "Fichiers absents")

    def test_ignores_urls_windows_paths_and_unsafe_playlist_data(self):
        self.write_playlist([
            {"path": "https://example.invalid/rom.zip", "label": "Remote"},
            {"path": r"C:\\ROMs\\Game.sfc", "label": "Windows"},
            {"path": "../relative.sfc", "label": "No base directory"},
            {"path": str(self.rom), "label": ""},
            None,
            "not-an-item",
        ])
        self.assertEqual(load_retroarch_games(self.playlist), [])

    def test_ignores_retroarch_favorites_and_history_lists(self):
        for name in ("content_favorites.lpl", "content_history.lpl"):
            path = self.playlists / name
            path.write_text(json.dumps({"items": [{
                "path": str(self.rom), "label": "Duplicate"
            }]}), encoding="utf-8")
            self.assertEqual(load_retroarch_games(path), [])

    def test_corrupt_oversized_or_non_json_playlists_are_ignored(self):
        self.playlist.write_text("{broken", encoding="utf-8")
        self.assertEqual(load_retroarch_games(self.playlist), [])
        self.playlist.write_text(" " * (16 * 1024 * 1024 + 1), encoding="utf-8")
        self.assertEqual(load_retroarch_games(self.playlist), [])


if __name__ == "__main__":
    unittest.main()
