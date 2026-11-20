"""Read-only checks for emulator BIOS, firmware and core prerequisites."""

import tempfile
import unittest
from pathlib import Path

from gaming.backend.emulator_prerequisites import detect_emulator_prerequisite_statuses


class EmulatorPrerequisiteTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.home = Path(self.temporary.name) / "home"
        self.home.mkdir()
        self.config_home = self.home / ".config"
        self.config_home.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def detect(self):
        return detect_emulator_prerequisite_statuses(
            home=self.home,
            config_home=self.config_home,
        )

    def flatpak_config(self, app_id, app_directory):
        directory = self.home / ".var/app" / app_id / "config" / app_directory
        directory.mkdir(parents=True)
        return directory

    def test_pcsx2_reports_bios_only_when_a_nonempty_regular_file_is_present(self):
        bios = self.flatpak_config("net.pcsx2.PCSX2", "PCSX2") / "bios"
        bios.mkdir()
        (bios / "ps2-bios.bin").write_bytes(b"firmware")
        results = self.detect()
        self.assertIn("fichier BIOS détecté", results[0])

    def test_pcsx2_ignores_empty_files_and_symlinks(self):
        bios = self.flatpak_config("net.pcsx2.PCSX2", "PCSX2") / "bios"
        bios.mkdir()
        (bios / "empty.bin").write_bytes(b"")
        target = self.home / "outside.bin"
        target.write_bytes(b"not a BIOS")
        (bios / "linked.bin").symlink_to(target)
        self.assertIn("BIOS PS2 à ajouter", self.detect()[0])

    def test_melonds_uses_saved_paths_and_checks_expected_dump_sizes(self):
        directory = self.flatpak_config("net.kuribo64.melonDS", "melonDS")
        files = {
            "arm9.bin": (4 * 1024, b"9"),
            "arm7.bin": (16 * 1024, b"7"),
            "ds-firmware.bin": (256 * 1024, b"f"),
        }
        for filename, (size, byte) in files.items():
            (self.home / filename).write_bytes(byte * size)
        (directory / "melonDS.toml").write_text(
            "[DS]\n"
            f'BIOS9Path = "{self.home / "arm9.bin"}"\n'
            f'BIOS7Path = "{self.home / "arm7.bin"}"\n'
            f'FirmwarePath = "{self.home / "ds-firmware.bin"}"\n',
            encoding="utf-8",
        )
        self.assertIn("BIOS et firmware DS détectés", self.detect()[1])

    def test_melonds_reports_incomplete_when_one_dump_is_missing_or_wrong_size(self):
        directory = self.flatpak_config("net.kuribo64.melonDS", "melonDS")
        bios9 = self.home / "arm9.bin"
        bios7 = self.home / "arm7.bin"
        firmware = self.home / "firmware.bin"
        bios9.write_bytes(b"9" * (4 * 1024))
        bios7.write_bytes(b"7" * (16 * 1024))
        firmware.write_bytes(b"f" * 1024)
        (directory / "melonDS.toml").write_text(
            "[DS]\n"
            f'BIOS9Path = "{bios9}"\n'
            f'BIOS7Path = "{bios7}"\n'
            f'FirmwarePath = "{firmware}"\n',
            encoding="utf-8",
        )
        self.assertIn("incomplets (2/3", self.detect()[1])

    def test_melonds_does_not_follow_a_symlink_to_a_bios_dump(self):
        directory = self.flatpak_config("net.kuribo64.melonDS", "melonDS")
        target = self.home / "arm9.bin"
        target.write_bytes(b"9" * (4 * 1024))
        (directory / "bios9.bin").symlink_to(target)
        (directory / "bios7.bin").write_bytes(b"7" * (16 * 1024))
        (directory / "firmware.bin").write_bytes(b"f" * (256 * 1024))
        # Default filenames are checked only when no path is configured.
        self.assertIn("BIOS et firmware DS à configurer", self.detect()[1])

    def test_rpcs3_detects_the_installed_dev_flash_structure(self):
        dev_flash = (
            self.flatpak_config("net.rpcs3.RPCS3", "rpcs3") / "dev_flash"
        )
        (dev_flash / "vsh").mkdir()
        self.assertIn("structure du firmware PS3 détectée", self.detect()[2])

    def test_rpcs3_does_not_treat_an_empty_dev_flash_directory_as_installed_firmware(self):
        dev_flash = (
            self.flatpak_config("net.rpcs3.RPCS3", "rpcs3") / "dev_flash"
        )
        dev_flash.mkdir()
        self.assertIn("firmware PS3 à installer", self.detect()[2])

    def test_retroarch_detects_user_selected_cores_folder_from_config(self):
        config_dir = self.flatpak_config("org.libretro.RetroArch", "retroarch")
        cores = self.home / "retroarch-cores"
        cores.mkdir()
        (cores / "snes9x_libretro.so").write_bytes(b"core")
        (config_dir / "retroarch.cfg").write_text(
            f'libretro_directory = "{cores}"\n',
            encoding="utf-8",
        )
        self.assertIn("1 cœur(s) détecté(s)", self.detect()[3])

    def test_retroarch_does_not_count_symlinked_or_empty_core_files(self):
        config_dir = self.config_home / "retroarch"
        config_dir.mkdir()
        cores = config_dir / "cores"
        cores.mkdir()
        (cores / "empty_libretro.so").write_bytes(b"")
        target = self.home / "core.so"
        target.write_bytes(b"core")
        (cores / "linked_libretro.so").symlink_to(target)
        self.assertIn("aucun cœur détecté", self.detect()[3])

    def test_statuses_never_read_rom_folders_or_return_private_file_paths(self):
        results = self.detect()
        self.assertEqual(len(results), 5)
        self.assertTrue(all(str(self.home) not in item for item in results))
        self.assertTrue(all("BIOS" in item or "firmware" in item or "cœur" in item for item in results))


if __name__ == "__main__":
    unittest.main()
