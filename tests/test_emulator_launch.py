"""Tests for safe local-game emulator launch command construction."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gaming.backend.emulator_launch import build_emulator_launch_command


class EmulatorLaunchTests(unittest.TestCase):
    def _setup(self, suffix=".nsp", name="Game"):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        home = Path(temporary.name)
        game_root = home / "Jeux"
        game_root.mkdir()
        game = game_root / f"{name}{suffix}"
        game.write_bytes(b"not inspected")
        app_id = "dev.eden_emu.eden"
        app_root = home / ".local/share/flatpak/app" / app_id
        app_root.mkdir(parents=True)
        return home, game, app_id

    def test_switch_file_uses_installed_eden_and_document_portal(self):
        home, game, app_id = self._setup()
        command, error = build_emulator_launch_command(
            game, home=home, data_home=home / ".local/share",
            flatpak_executable="/usr/bin/flatpak",
        )
        self.assertEqual(error, "")
        self.assertEqual(
            command,
            ["/usr/bin/flatpak", "run", "--file-forwarding", app_id,
             "@@", str(game.resolve()), "@@"],
        )

    def test_known_console_formats_map_to_expected_emulators(self):
        cases = {
            ".rvz": "org.DolphinEmu.dolphin-emu",
            ".wua": "info.cemu.Cemu",
            ".nsp": "dev.eden_emu.eden",
            ".cso": "org.ppsspp.PPSSPP",
        }
        for suffix, app_id in cases.items():
            with self.subTest(suffix=suffix):
                home, game, _ = self._setup(suffix=suffix)
                app = home / ".local/share/flatpak/app" / app_id
                app.mkdir(parents=True, exist_ok=True)
                command, error = build_emulator_launch_command(
                    game, home=home, data_home=home / ".local/share",
                    flatpak_executable="flatpak",
                )
                self.assertEqual(error, "")
                self.assertEqual(command[3], app_id)

    def test_custom_named_flatpak_installation_is_used_explicitly(self):
        home, game, app_id = self._setup()
        default_app = home / ".local/share/flatpak/app" / app_id
        default_app.rmdir()
        custom_root = home / "external-drive/flatpak"
        (custom_root / "app" / app_id).mkdir(parents=True)
        config_dir = home / "flatpak-config"
        config_dir.mkdir()
        (config_dir / "games.conf").write_text(
            '[Installation "games"]\n'
            f"Path={custom_root}\n"
            "DisplayName=Games drive\n"
            "StorageType=harddisk\n",
            encoding="utf-8",
        )

        command, error = build_emulator_launch_command(
            game,
            home=home,
            data_home=home / ".local/share",
            flatpak_executable="/usr/bin/flatpak",
            system_installations_config_dir=config_dir,
        )

        self.assertEqual(error, "")
        self.assertEqual(
            command,
            ["/usr/bin/flatpak", "--installation=games", "run",
             "--file-forwarding", app_id, "@@", str(game.resolve()), "@@"],
        )

    def test_default_user_installation_keeps_flatpak_default_command(self):
        home, game, app_id = self._setup()
        command, error = build_emulator_launch_command(
            game,
            home=home,
            data_home=home / ".local/share",
            flatpak_executable="flatpak",
            system_installations_config_dir=home / "missing-config",
        )
        self.assertEqual(error, "")
        self.assertEqual(command[1:4], ["run", "--file-forwarding", app_id])

    def test_malformed_and_symlinked_custom_installations_are_ignored(self):
        home, game, app_id = self._setup()
        (home / ".local/share/flatpak/app" / app_id).rmdir()
        custom_root = home / "external-drive/flatpak"
        (custom_root / "app" / app_id).mkdir(parents=True)
        config_dir = home / "flatpak-config"
        config_dir.mkdir()
        (config_dir / "bad.conf").write_text(
            '[Installation "games"]\nnot valid ini',
            encoding="utf-8",
        )
        (config_dir / "link.conf").symlink_to(config_dir / "bad.conf")
        command, error = build_emulator_launch_command(
            game,
            home=home,
            data_home=home / ".local/share",
            flatpak_executable="flatpak",
            system_installations_config_dir=config_dir,
        )
        self.assertIsNone(command)
        self.assertIn("n'est pas installé", error)

    def test_ambiguous_or_unsupported_formats_are_not_guessed(self):
        home, game, _ = self._setup(suffix=".iso")
        command, error = build_emulator_launch_command(
            game, home=home, data_home=home / ".local/share",
            flatpak_executable="flatpak",
        )
        self.assertIsNone(command)
        self.assertIn("Aucun émulateur", error)

    def test_missing_emulator_is_not_installed_automatically(self):
        home, game, _ = self._setup()
        (home / ".local/share/flatpak/app/dev.eden_emu.eden").rmdir()
        command, error = build_emulator_launch_command(
            game, home=home, data_home=home / ".local/share",
            flatpak_executable="flatpak",
        )
        self.assertIsNone(command)
        self.assertIn("n'est pas installé", error)

    def test_rejects_files_outside_library_roots_and_symlinks(self):
        home, game, _ = self._setup()
        outside = home / "outside.nsp"
        outside.write_bytes(b"not inspected")
        command, _ = build_emulator_launch_command(
            outside, home=home, data_home=home / ".local/share",
            flatpak_executable="flatpak",
        )
        self.assertIsNone(command)
        link = home / "Jeux" / "linked.nsp"
        link.symlink_to(outside)
        command, _ = build_emulator_launch_command(
            link, home=home, data_home=home / ".local/share",
            flatpak_executable="flatpak",
        )
        self.assertIsNone(command)

    def test_missing_flatpak_is_reported(self):
        home, game, _ = self._setup()
        with patch("gaming.backend.emulator_launch.shutil.which", return_value=None):
            command, error = build_emulator_launch_command(
                game, home=home, data_home=home / ".local/share"
            )
        self.assertIsNone(command)
        self.assertIn("Flatpak", error)


if __name__ == "__main__":
    unittest.main()
