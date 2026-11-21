"""Tests for read-only detection of curated optional emulator installations."""

import tempfile
import unittest
from pathlib import Path

from gaming.backend.emulator_inventory import (
    build_emulator_frontend_command,
    detect_emulator_installations,
)


class EmulatorInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.data_home = self.root / "data"
        self.system_root = self.root / "system-flatpak-apps"
        self.which_map = {}

    def tearDown(self):
        self.temporary.cleanup()

    def lookup(self, binary):
        return self.which_map.get(binary)

    def deploy(self, root, app_id):
        (root / app_id / "x86_64" / "stable" / "abcdef" / "files").mkdir(parents=True)

    def detect(self):
        return detect_emulator_installations(
            which=self.lookup,
            data_home=self.data_home,
            system_flatpak_root=self.system_root,
        )

    def test_reports_all_seven_emulators_as_not_detected_by_default(self):
        results = self.detect()
        self.assertEqual(len(results), 7)
        self.assertTrue(all(not item["scope"] for item in results))
        self.assertTrue(all("NON DÉTECTÉ" in item["status"] for item in results))

    def test_detects_flatpak_user_and_system_deployments(self):
        self.deploy(self.data_home / "flatpak/app", "org.libretro.RetroArch")
        self.deploy(self.system_root, "net.pcsx2.PCSX2")
        results = {item["id"]: item for item in self.detect()}

        self.assertEqual(results["org.libretro.RetroArch"]["scope"], "FLATPAK UTILISATEUR")
        self.assertEqual(results["net.pcsx2.PCSX2"]["scope"], "FLATPAK SYSTÈME")
        self.assertEqual(results["org.ppsspp.PPSSPP"]["scope"], "")

    def test_detects_eden_flatpak_deployment(self):
        self.deploy(self.data_home / "flatpak/app", "dev.eden_emu.eden")
        results = {item["id"]: item for item in self.detect()}
        self.assertEqual(
            results["dev.eden_emu.eden"]["scope"], "FLATPAK UTILISATEUR"
        )
        self.assertEqual(
            results["dev.eden_emu.eden"]["status"],
            "EDEN · DISPONIBLE (FLATPAK UTILISATEUR)",
        )

    def test_ignores_flatpak_ref_directory_without_deployed_files(self):
        (self.data_home / "flatpak/app/org.libretro.RetroArch/x86_64/stable").mkdir(parents=True)
        results = {item["id"]: item for item in self.detect()}
        self.assertEqual(results["org.libretro.RetroArch"]["scope"], "")

    def test_native_executable_takes_precedence_over_flatpak(self):
        self.deploy(self.data_home / "flatpak/app", "org.DolphinEmu.dolphin-emu")
        self.which_map["dolphin-emu"] = "/usr/bin/dolphin-emu"
        results = {item["id"]: item for item in self.detect()}

        self.assertEqual(results["org.DolphinEmu.dolphin-emu"]["scope"], "NATIF")
        self.assertIn("DISPONIBLE (NATIF)", results["org.DolphinEmu.dolphin-emu"]["status"])

    def test_checks_known_alternative_executable_names(self):
        self.which_map["pcsx2"] = "/usr/bin/pcsx2"
        self.which_map["ppsspp"] = "/usr/bin/ppsspp"
        results = {item["id"]: item for item in self.detect()}

        self.assertEqual(results["net.pcsx2.PCSX2"]["scope"], "NATIF")
        self.assertEqual(results["org.ppsspp.PPSSPP"]["scope"], "NATIF")

    def test_ignores_flatpak_user_configuration_directory_without_deployment(self):
        (self.data_home / "flatpak/app").mkdir(parents=True)
        results = self.detect()
        self.assertTrue(all(not item["scope"] for item in results))

    def test_does_not_scan_rom_folders_or_launch_processes(self):
        # The detector has no ROM path input and accepts only an executable lookup.
        results = self.detect()
        self.assertTrue(all(set(item) == {"id", "name", "scope", "status"} for item in results))


    def test_frontend_command_prefers_native_eden_executable(self):
        self.deploy(self.data_home / "flatpak/app", "dev.eden_emu.eden")
        self.which_map["eden"] = "/usr/bin/eden"
        self.which_map["flatpak"] = "/usr/bin/flatpak"
        command = build_emulator_frontend_command(
            "dev.eden_emu.eden",
            which=self.lookup,
            data_home=self.data_home,
            system_flatpak_root=self.system_root,
        )
        self.assertEqual(command, ["/usr/bin/eden"])

    def test_frontend_command_opens_deployed_user_flatpak_eden(self):
        self.deploy(self.data_home / "flatpak/app", "dev.eden_emu.eden")
        self.which_map["flatpak"] = "/usr/bin/flatpak"
        command = build_emulator_frontend_command(
            "dev.eden_emu.eden",
            which=self.lookup,
            data_home=self.data_home,
            system_flatpak_root=self.system_root,
        )
        self.assertEqual(command, ["/usr/bin/flatpak", "run", "dev.eden_emu.eden"])

    def test_frontend_command_opens_deployed_system_flatpak_eden(self):
        self.deploy(self.system_root, "dev.eden_emu.eden")
        self.which_map["flatpak"] = "/usr/bin/flatpak"
        command = build_emulator_frontend_command(
            "dev.eden_emu.eden",
            which=self.lookup,
            data_home=self.data_home,
            system_flatpak_root=self.system_root,
        )
        self.assertEqual(command, ["/usr/bin/flatpak", "run", "dev.eden_emu.eden"])

    def test_frontend_command_never_guesses_or_runs_uninstalled_emulator(self):
        self.which_map["flatpak"] = "/usr/bin/flatpak"
        command = build_emulator_frontend_command(
            "dev.eden_emu.eden",
            which=self.lookup,
            data_home=self.data_home,
            system_flatpak_root=self.system_root,
        )
        self.assertEqual(command, [])
        self.assertEqual(
            build_emulator_frontend_command(
                "arbitrary.application",
                which=self.lookup,
                data_home=self.data_home,
                system_flatpak_root=self.system_root,
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
