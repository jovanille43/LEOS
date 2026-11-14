"""Tests for safe, automatic filing of completed game downloads."""

import tempfile
import unittest
from pathlib import Path

from gaming.backend.download_organizer import (
    DownloadOrganizer,
    resolve_download_directory,
)


class DownloadOrganizerTests(unittest.TestCase):
    def test_resolves_custom_xdg_download_directory_without_shell_evaluation(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home / ".config"
            config.mkdir()
            (config / "user-dirs.dirs").write_text(
                'XDG_DOWNLOAD_DIR="$HOME/Téléchargements"\n',
                encoding="utf-8",
            )
            expected = home / "Téléchargements"
            self.assertEqual(resolve_download_directory(home, config), expected)

    def test_rejects_xdg_download_path_outside_home(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            home.mkdir()
            config = home / ".config"
            config.mkdir()
            (config / "user-dirs.dirs").write_text(
                'XDG_DOWNLOAD_DIR="$HOME/../../outside"\n',
                encoding="utf-8",
            )
            self.assertEqual(resolve_download_directory(home, config), home / "Downloads")

    def test_uses_existing_french_downloads_folder_as_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            downloads = home / "Téléchargements"
            downloads.mkdir()
            self.assertEqual(resolve_download_directory(home), downloads)

    def test_moves_completed_wii_u_game_after_stability_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            downloads = home / "Downloads"
            downloads.mkdir()
            game = downloads / "The Legend of Zelda.wua"
            game.write_bytes(b"mock game data")
            modified = game.stat().st_mtime

            organizer = DownloadOrganizer(
                downloads, home / "Emulation" / "ROMs", home=home,
                stability_seconds=15,
            )
            self.assertEqual(organizer.poll(now=modified + 1), [])
            self.assertEqual(organizer.poll(now=modified + 10), [])
            moved = organizer.poll(now=modified + 20)

            self.assertEqual(len(moved), 1)
            target = home / "Emulation" / "ROMs" / "Nintendo" / "Wii U" / game.name
            self.assertEqual(Path(moved[0]["destination"]), target)
            self.assertTrue(target.is_file())
            self.assertFalse(game.exists())

    def test_classifies_console_specific_download_formats(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            downloads = home / "Downloads"
            downloads.mkdir()
            files = {
                "Metroid.gba": ("Nintendo", "Game Boy Advance"),
                "Mario.wbfs": ("Nintendo", "Wii"),
                "Sonic.md": ("SEGA", "Mega Drive"),
                "Lumines.cso": ("PlayStation", "PSP"),
            }
            modified = {}
            for filename in files:
                path = downloads / filename
                path.write_bytes(b"game")
                modified[filename] = path.stat().st_mtime
            organizer = DownloadOrganizer(
                downloads, home / "Emulation" / "ROMs", home=home,
                stability_seconds=0,
            )
            moved = []
            latest_mtime = max(modified.values())
            for offset in (1, 2, 3):
                moved.extend(organizer.poll(now=latest_mtime + offset))
            self.assertEqual(len(moved), len(files))
            for filename, (system, console) in files.items():
                target = home / "Emulation" / "ROMs" / system / console / filename
                self.assertTrue(target.is_file(), filename)

    def test_does_not_move_ambiguous_formats_or_archives(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            downloads = home / "Downloads"
            downloads.mkdir()
            names = ("Disc.iso", "Track.bin", "Set.zip", "Archive.7z", "Game.chd")
            for name in names:
                (downloads / name).write_bytes(b"data")
            organizer = DownloadOrganizer(
                downloads, home / "Emulation" / "ROMs", home=home,
                stability_seconds=0,
            )
            organizer.poll(now=10_000)
            self.assertEqual(organizer.poll(now=10_020), [])
            self.assertTrue(all((downloads / name).is_file() for name in names))

    def test_ignores_browser_partial_downloads_and_zero_byte_files(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            downloads = home / "Downloads"
            downloads.mkdir()
            (downloads / "Game.gba.crdownload").write_bytes(b"partial")
            (downloads / "Game.gba.part").write_bytes(b"partial")
            (downloads / "Empty.gba").touch()
            organizer = DownloadOrganizer(
                downloads, home / "Emulation" / "ROMs", home=home,
                stability_seconds=0,
            )
            self.assertEqual(organizer.poll(now=10_000), [])
            self.assertEqual(organizer.poll(now=10_020), [])
            self.assertEqual(len(list(downloads.iterdir())), 3)

    def test_does_not_overwrite_existing_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            downloads = home / "Downloads"
            destination = home / "Emulation" / "ROMs" / "Nintendo" / "Wii U"
            downloads.mkdir()
            destination.mkdir(parents=True)
            original = destination / "Game.wua"
            original.write_bytes(b"keep this")
            source = downloads / "Game.wua"
            source.write_bytes(b"new data")
            modified = source.stat().st_mtime
            organizer = DownloadOrganizer(
                downloads, home / "Emulation" / "ROMs", home=home,
                stability_seconds=0,
            )
            organizer.poll(now=modified + 1)
            moved = organizer.poll(now=modified + 2)
            # Two unchanged rechecks are required, so one further poll is needed.
            if not moved:
                moved = organizer.poll(now=modified + 3)
            self.assertEqual(len(moved), 1)
            self.assertEqual(original.read_bytes(), b"keep this")
            self.assertTrue((destination / "Game (2).wua").is_file())

    def test_ignores_symbolic_link_downloads(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            downloads = home / "Downloads"
            downloads.mkdir()
            outside = home / "outside.wua"
            outside.write_bytes(b"keep")
            linked = downloads / "linked.wua"
            try:
                linked.symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("Symbolic links unavailable")
            organizer = DownloadOrganizer(
                downloads, home / "Emulation" / "ROMs", home=home,
                stability_seconds=0,
            )
            organizer.poll(now=10_000)
            self.assertEqual(organizer.poll(now=10_020), [])
            self.assertTrue(linked.is_symlink())
            self.assertEqual(outside.read_bytes(), b"keep")

    def test_rejects_overlapping_download_and_emulation_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            downloads = home / "Emulation" / "Downloads"
            downloads.mkdir(parents=True)
            game = downloads / "Game.wua"
            game.write_bytes(b"game")
            organizer = DownloadOrganizer(
                downloads, home / "Emulation", home=home,
                stability_seconds=0,
            )
            self.assertEqual(organizer.poll(now=10_000), [])
            self.assertEqual(organizer.poll(now=10_020), [])
            self.assertTrue(game.exists())


if __name__ == "__main__":
    unittest.main()
