"""Tests for the read-only hardware inventory."""

import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from control_center import hardware


class HardwareInventoryTests(unittest.TestCase):
    def test_hardware_text_reader_rejects_oversized_files(self):
        with tempfile.NamedTemporaryFile() as stream:
            stream.write(b"x" * (hardware.MAX_HARDWARE_TEXT_BYTES + 1))
            stream.flush()
            self.assertEqual(hardware._read(stream.name), "")

    def test_hardware_text_reader_keeps_valid_utf8_and_tolerates_kernel_bytes(self):
        with tempfile.NamedTemporaryFile() as stream:
            stream.write(b"Model: Test CPU" + bytes([0xFF]))
            stream.flush()
            self.assertEqual(hardware._read(stream.name), "Model: Test CPU" + chr(0xFFFD))

    def test_snapshot_exposes_all_dashboard_fields(self):
        snapshot = hardware.collect_hardware_snapshot()
        expected = {
            "cpu", "cpuThreads", "cpuCores", "memory", "storage", "gpu", "displayCount", "displays", "vulkan",
            "memoryTotal", "architecture", "firmware", "gamingBaseline",
            "operatingSystem", "kernel", "bluetooth", "bluetoothDevices",
            "audioServer", "audioOutput", "audioInputs", "controllers", "battery",
            "usbDevices", "network",
        }
        self.assertEqual(set(snapshot), expected)
        self.assertTrue(all(isinstance(value, str) for value in snapshot.values()))

    def test_cpu_details_reads_arm_processor_field_and_online_cpu_list(self):
        responses = {
            "/proc/cpuinfo": "Processor : ARMv8 Processor rev 1 (v8l)\n",
            "/sys/devices/system/cpu/online": "0-5",
        }
        with patch.object(hardware, "_read", side_effect=lambda path: responses.get(str(path), "")):
            with patch.object(hardware.os, "cpu_count", return_value=99):
                self.assertEqual(
                    hardware._cpu_details(),
                    ("ARMv8 Processor rev 1 (v8l)", "6 thread(s)"),
                )

    def test_cpu_details_uses_device_tree_model_when_proc_has_no_model(self):
        responses = {
            "/proc/cpuinfo": "processor : 0\nprocessor : 1\n",
            "/sys/firmware/devicetree/base/model": "Example ARM Board\x00",
        }
        with patch.object(hardware, "_read", side_effect=lambda path: responses.get(str(path), "")):
            self.assertEqual(
                hardware._cpu_details(),
                ("Example ARM Board", "2 thread(s)"),
            )

    def test_architecture_normalizes_common_x86_and_arm_names(self):
        self.assertEqual(hardware._architecture_details("AMD64"), "x86_64")
        self.assertEqual(hardware._architecture_details("x64"), "x86_64")
        self.assertEqual(hardware._architecture_details("aarch64"), "ARM64")
        self.assertEqual(hardware._architecture_details(""), "Indisponible")

    def test_firmware_detection_requires_exposed_efi_directory(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            efi = root / "efi"
            efi.mkdir()
            self.assertEqual(hardware._firmware_details(efi), "UEFI")
            self.assertEqual(hardware._firmware_details(root / "missing"), "UEFI non détecté")

    def test_cpu_topology_counts_physical_cores_separately_from_threads(self):
        blocks = []
        for core in range(4):
            for thread in range(2):
                blocks.append(
                    f"processor : {core * 2 + thread}\nphysical id : 0\ncore id : {core}"
                )
        physical, logical = hardware._cpu_topology("\n\n".join(blocks))
        self.assertEqual((physical, logical), (4, 8))
        self.assertIn("4 cœur(s) physique(s)", hardware._cpu_core_details(physical, logical))
        self.assertIn("8 threads logiques", hardware._cpu_core_details(physical, logical))

    def test_cpu_topology_does_not_guess_physical_cores_from_logical_threads(self):
        physical, logical = hardware._cpu_topology("processor : 0\n\nprocessor : 1")
        self.assertIsNone(physical)
        self.assertEqual(logical, 2)
        self.assertEqual(
            hardware._cpu_core_details(physical, logical),
            "Cœurs physiques indisponibles",
        )

    def test_linux_cpu_list_parser_handles_ranges_and_invalid_entries(self):
        self.assertEqual(
            hardware._parse_cpu_list("0-3, 6,8-9,broken,-2,12-10"),
            {0, 1, 2, 3, 6, 8, 9},
        )

    def test_sysfs_topology_counts_online_cores_across_packages(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "online").write_text("0-3,8-9", encoding="utf-8")
            for cpu_id, package, core in [
                (0, 0, 0), (1, 0, 0), (2, 0, 1),
                (3, 0, 1), (8, 1, 0), (9, 1, 0),
            ]:
                topology = root / f"cpu{cpu_id}" / "topology"
                topology.mkdir(parents=True)
                (topology / "physical_package_id").write_text(str(package), encoding="utf-8")
                (topology / "core_id").write_text(str(core), encoding="utf-8")

            self.assertEqual(hardware._cpu_topology_from_sysfs(root), (3, 6))
            self.assertEqual(hardware._cpu_topology(sysfs_root=root), (3, 6))

    def test_sysfs_topology_uses_arm_cluster_ids_when_package_ids_are_absent(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "online").write_text("0-3", encoding="utf-8")
            for cpu_id, cluster, core in [
                (0, 0, 0), (1, 0, 1), (2, 1, 0), (3, 1, 1),
            ]:
                topology = root / f"cpu{cpu_id}" / "topology"
                topology.mkdir(parents=True)
                (topology / "cluster_id").write_text(str(cluster), encoding="utf-8")
                (topology / "core_id").write_text(str(core), encoding="utf-8")

            self.assertEqual(hardware._cpu_topology_from_sysfs(root), (4, 4))

    def test_sysfs_topology_reports_unknown_cores_instead_of_guessing(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "online").write_text("0-1", encoding="utf-8")
            for cpu_id in range(2):
                (root / f"cpu{cpu_id}" / "topology").mkdir(parents=True)
            self.assertEqual(hardware._cpu_topology_from_sysfs(root), (None, 2))

    def test_sysfs_topology_does_not_under_count_mixed_partial_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "online").write_text("0-2", encoding="utf-8")

            first = root / "cpu0" / "topology"
            first.mkdir(parents=True)
            (first / "physical_package_id").write_text("0", encoding="utf-8")
            (first / "core_id").write_text("0", encoding="utf-8")

            second = root / "cpu1" / "topology"
            second.mkdir(parents=True)
            (second / "physical_package_id").write_text("0", encoding="utf-8")
            (second / "core_id").write_text("1", encoding="utf-8")

            # A third online CPU exposes a core ID but no package/cluster ID.
            third = root / "cpu2" / "topology"
            third.mkdir(parents=True)
            (third / "core_id").write_text("0", encoding="utf-8")

            self.assertEqual(hardware._cpu_topology_from_sysfs(root), (None, 3))

    def test_memory_total_parser_and_gaming_baseline_are_conservative(self):
        with patch.object(
            hardware, "_read",
            return_value="MemTotal:       16384000 kB\nMemAvailable:    8192000 kB\n",
        ):
            total = hardware._memory_total_bytes()
        self.assertEqual(total, 16384000 * 1024)
        self.assertEqual(hardware._memory_total_details(total), "15.6 Gio")

        devices = [("GPU de test", (1, 3, 280))]
        passed = hardware._gaming_baseline_assessment(
            "x86_64", "UEFI", total, 4, 60_000_000_000, devices
        )
        self.assertIn("Indicateurs vérifiables au niveau des seuils", passed)
        self.assertIn("fréquence CPU de référence non certifiée", passed)
        self.assertIn("type de support de stockage non vérifié", passed)
        self.assertNotIn("Sous le seuil Gaming", passed)

        unsupported = hardware._gaming_baseline_assessment(
            "ARM64", "UEFI non détecté", 4 * 1024 ** 3,
            physical_cores=2,
            storage_free_bytes=20_000_000_000,
            vulkan_devices=[("GPU ancien", (1, 2, 0))],
        )
        self.assertIn("ARM64 hors cible", unsupported)
        self.assertIn("moins de 8 Go de RAM", unsupported)
        self.assertIn("UEFI non détecté", unsupported)
        self.assertIn("moins de 4 cœurs physiques", unsupported)
        self.assertIn("moins de 50 Go libres", unsupported)
        self.assertIn("Vulkan 1.3+", unsupported)

    def test_missing_baseline_data_is_reported_as_unknown_not_as_failure(self):
        result = hardware._gaming_baseline_assessment(
            "x86_64", "UEFI", 16 * 1024 ** 3
        )
        self.assertIn("Contrôle Gaming incomplet", result)
        self.assertIn("nombre de cœurs physiques non vérifiable", result)
        self.assertIn("prise en charge Vulkan 1.3+ non vérifiable", result)
        self.assertNotIn("moins de 4 cœurs", result)

    def test_storage_reports_free_space_without_claiming_drive_type(self):
        usage = SimpleNamespace(total=200 * 1024 ** 3, used=100 * 1024 ** 3, free=100 * 1024 ** 3)
        with patch.object(hardware.shutil, "disk_usage", return_value=usage):
            label, free = hardware._storage_details()
        self.assertEqual(free, usage.free)
        self.assertIn("Gio libres sur /", label)

    def test_storage_unavailable_is_non_fatal(self):
        with patch.object(hardware.shutil, "disk_usage", side_effect=OSError):
            self.assertEqual(hardware._storage_details(), ("Indisponible", None))

    def test_vulkan_parser_reads_per_device_api_version(self):
        output = (
            "Devices:\n========\n"
            "GPU0:\n"
            "    deviceName = AMD Radeon Test\n"
            "    apiVersion = 1.3.280 (4206856)\n"
            "GPU1:\n"
            "    deviceName = Intel Graphics Test\n"
            "    apiVersion = 1.2.198 (4202694)\n"
        )
        self.assertEqual(
            hardware._parse_vulkan_devices(output),
            [
                ("AMD Radeon Test", (1, 3, 280)),
                ("Intel Graphics Test", (1, 2, 198)),
            ],
        )

    def test_vulkan_probe_reports_missing_tool_without_crashing(self):
        with patch.object(hardware.shutil, "which", return_value=None):
            self.assertEqual(
                hardware._vulkan_snapshot(),
                ("Non vérifiable (outil vulkaninfo absent)", None),
            )

    def test_vulkan_probe_keeps_unknown_device_version_unknown(self):
        output = "GPU0:\n    deviceName = GPU Test\n"
        with patch.object(hardware.shutil, "which", return_value="/usr/bin/vulkaninfo"):
            with patch.object(hardware, "_run", return_value=output):
                label, devices = hardware._vulkan_snapshot()
        self.assertIn("version Vulkan inconnue", label)
        self.assertEqual(devices, [("GPU Test", None)])

    def test_gpu_inventory_includes_multi_digit_drm_card_indices_only(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            card0 = root / "card0" / "device"
            card10 = root / "card10" / "device"
            connector = root / "card0-DP-1" / "device"
            for device, vendor in [
                (card0, "0x1002"),
                (card10, "0x10de"),
                (connector, "0x8086"),
            ]:
                device.mkdir(parents=True)
                (device / "vendor").write_text(vendor, encoding="utf-8")

            with patch.object(
                hardware.Path, "glob",
                return_value=[card0, card10, connector],
            ):
                self.assertEqual(
                    hardware._gpu_details(),
                    "AMD · NVIDIA",
                )

    def test_gpu_inventory_distinguishes_identical_cards_by_pci_address(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            drm = root / "drm"
            devices = []
            for card, pci in [
                ("card0", "0000:01:00.0"),
                ("card1", "0000:02:00.0"),
            ]:
                target = root / "devices" / "pci0000:00" / pci
                target.mkdir(parents=True)
                (target / "vendor").write_text("0x10de", encoding="ascii")
                (target / "device").write_text("0x2503", encoding="ascii")
                card_device = drm / card / "device"
                card_device.parent.mkdir(parents=True)
                card_device.symlink_to(target)
                devices.append(card_device)

            lspci = (
                "0000:01:00.0 VGA compatible controller [0300]: "
                "NVIDIA Corporation GA106 [GeForce RTX 3060] [10de:2503]\n"
                "0000:02:00.0 3D controller [0302]: "
                "NVIDIA Corporation GA106 [GeForce RTX 3060] [10de:2503]\n"
            )
            with patch.object(hardware.Path, "glob", return_value=devices):
                with patch.object(hardware, "_run", return_value=lspci):
                    result = hardware._gpu_details()

        self.assertEqual(
            result,
            "NVIDIA Corporation GA106 [GeForce RTX 3060] [0000:01:00.0] · "
            "NVIDIA Corporation GA106 [GeForce RTX 3060] [0000:02:00.0]",
        )

    def test_gpu_inventory_deduplicates_multiple_drm_nodes_for_one_pci_device(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "devices" / "pci0000:00" / "0000:01:00.0"
            target.mkdir(parents=True)
            (target / "vendor").write_text("0x10de", encoding="ascii")
            (target / "device").write_text("0x2503", encoding="ascii")
            devices = []
            for card in ("card0", "card1"):
                card_device = root / card / "device"
                card_device.parent.mkdir(parents=True)
                card_device.symlink_to(target)
                devices.append(card_device)

            lspci = (
                "0000:01:00.0 VGA compatible controller [0300]: "
                "NVIDIA Corporation GA106 [GeForce RTX 3060] [10de:2503]\n"
            )
            with patch.object(hardware.Path, "glob", return_value=devices):
                with patch.object(hardware, "_run", return_value=lspci):
                    result = hardware._gpu_details()

        self.assertEqual(
            result,
            "NVIDIA Corporation GA106 [GeForce RTX 3060]",
        )

    def test_lspci_gpu_parser_maps_models_by_full_pci_address(self):
        output = (
            "0000:03:00.0 VGA compatible controller [0300]: "
            "NVIDIA Corporation GA106 [GeForce RTX 3060] [10de:2503] (rev a1)\n"
            "0000:00:02.0 Display controller [0380]: "
            "Intel Corporation UHD Graphics 770 [8086:4680]\n"
            "0000:04:00.0 Ethernet controller [0200]: "
            "Example Network Adapter [1234:5678]\n"
        )
        self.assertEqual(
            hardware._parse_lspci_gpu_devices(output),
            {
                "0000:03:00.0": "NVIDIA Corporation GA106 [GeForce RTX 3060]",
                "0000:00:02.0": "Intel Corporation UHD Graphics 770",
            },
        )

    def test_kscreen_parser_reports_active_modes_geometry_and_scale(self):
        output = (
            "Output: 1 eDP-1 enabled connected priority 1 Panel\n"
            "    Modes: 0: \x1b[32m1920x1080@60.00*\x1b[0m 1: 1280x720@60.00\n"
            "    Geometry: 0,0 1920x1080\n"
            "    Scale: 1.25\n"
            "    Rotation: 1\n"
            "Output: 2 DP-1 enabled connected priority 2 DisplayPort\n"
            "    Modes: 0: 2560x1440@144.00* 1: 1920x1080@60.00\n"
            "    Geometry: 1920,0 2560x1440\n"
            "    Scale: 1\n"
        )
        self.assertEqual(
            hardware._parse_kscreen_displays(output),
            (
                "2",
                "eDP-1 · actif · 1920x1080 à 60 Hz · géométrie 0,0 1920x1080 · échelle 1.25 | "
                "DP-1 · actif · 2560x1440 à 144 Hz · géométrie 1920,0 2560x1440 · échelle 1",
            ),
        )

    def test_kscreen_parser_preserves_large_integer_display_scale(self):
        output = (
            "Output: 1 DP-1 enabled connected priority 1 DisplayPort\n"
            "    Modes: 0: 1920x1080@60.00*\n"
            "    Scale: 10.0\n"
        )
        self.assertEqual(
            hardware._parse_kscreen_displays(output),
            ("1", "DP-1 · actif · 1920x1080 à 60 Hz · échelle 10"),
        )

        output = (
            "Output: 3 HDMI-A-1 connected priority 3 HDMI\n"
            "    Modes: 0: 3840x2160@60.00*\n"
        )
        self.assertEqual(
            hardware._parse_kscreen_displays(output),
            ("1", "HDMI-A-1 · connecté, inactif · 3840x2160 à 60 Hz"),
        )

    def test_kscreen_parser_returns_none_when_command_output_is_unavailable(self):
        self.assertIsNone(hardware._parse_kscreen_displays(""))
        self.assertIsNone(hardware._parse_kscreen_displays("no output data"))

    def test_display_inventory_prefers_kscreen_active_state_over_drm_fallback(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            connector = root / "card0-DP-1"
            connector.mkdir()
            (connector / "status").write_text("disconnected", encoding="ascii")

            kscreen_output = (
                "Output: 1 DP-1 enabled connected priority 1 DisplayPort\n"
                "    Modes: 0: 2560x1440@144.00*\n"
                "    Geometry: 0,0 2560x1440\n"
                "    Scale: 1.25\n"
            )
            self.assertEqual(
                hardware._display_details(root, kscreen_output=kscreen_output),
                (
                    "1",
                    "DP-1 · actif · 2560x1440 à 144 Hz · "
                    "géométrie 0,0 2560x1440 · échelle 1.25",
                ),
            )

    def test_display_inventory_lists_connected_outputs_and_available_modes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, status, enabled, modes in [
                ("card0-eDP-1", "connected", "enabled", "1920x1080\n2560x1440\n"),
                ("card1-DP-1", "connected", "disabled", "3840x2160\n1920x1080\n"),
                ("card1-HDMI-A-1", "disconnected", "disabled", ""),
            ]:
                connector = root / name
                connector.mkdir()
                (connector / "status").write_text(status, encoding="ascii")
                (connector / "enabled").write_text(enabled, encoding="ascii")
                (connector / "modes").write_text(modes, encoding="ascii")

            self.assertEqual(
                hardware._display_details(root, kscreen_output=""),
                (
                    "2",
                    "eDP-1 · actif · modes disponibles : 1920x1080, 2560x1440 | "
                    "DP-1 · connecté, non activé · modes disponibles : 3840x2160, 1920x1080",
                ),
            )

    def test_display_inventory_reports_no_connected_screens_without_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            connector = root / "card0-HDMI-A-1"
            connector.mkdir()
            (connector / "status").write_text("disconnected", encoding="ascii")
            self.assertEqual(
                hardware._display_details(root, kscreen_output=""),
                ("0", "Aucun écran connecté détecté par DRM"),
            )

    def test_display_inventory_reports_unknown_when_drm_has_no_connectors(self):
        with tempfile.TemporaryDirectory() as temporary:
            self.assertEqual(
                hardware._display_details(Path(temporary), kscreen_output=""),
                ("Non vérifiable", "Aucun connecteur d'écran exposé par DRM"),
            )

    def test_display_inventory_does_not_treat_missing_connector_status_as_disconnected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "card0-DP-1").mkdir()
            self.assertEqual(
                hardware._display_details(root, kscreen_output=""),
                ("Non vérifiable", "État des connecteurs non exposé par DRM"),
            )

    def test_display_inventory_keeps_connected_screen_when_modes_are_unavailable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            connector = root / "card0-DP-1"
            connector.mkdir()
            (connector / "status").write_text("connected", encoding="ascii")
            self.assertEqual(
                hardware._display_details(root, kscreen_output=""),
                ("1", "DP-1 · connecté · modes non exposés"),
            )

    def test_bluetooth_reports_inactive_service_without_claiming_devices(self):
        with patch.object(hardware, "_run", return_value="inactive"):
            self.assertEqual(
                hardware._bluetooth_details(),
                ("Inactif", "Aucun périphérique connecté détecté"),
            )

    def test_bluetooth_lists_connected_device_names(self):
        responses = iter([
            "active",
            "Controller AA:BB:CC:DD:EE:FF\n\tPowered: yes",
            "Device 11:22:33:44:55:66 Casque LEOS",
        ])
        with patch.object(hardware, "_run", side_effect=lambda *_args, **_kwargs: next(responses)):
            self.assertEqual(
                hardware._bluetooth_details(),
                ("Activé", "Casque LEOS"),
            )

    def test_audio_handles_missing_pipewire_or_pulseaudio(self):
        with patch.object(hardware, "_run", return_value=""):
            self.assertEqual(
                hardware._audio_details(),
                ("Serveur audio indisponible", "Sortie non détectée", "Entrée non détectée"),
            )

    def test_audio_reports_default_output_and_input_count(self):
        responses = iter([
            "Server Name: PulseAudio (on PipeWire 1.2)\nDefault Sink: alsa_output.pci-1.analog-stereo",
            "0 alsa_output.pci-1.analog-stereo module-alsa-card.c s16le 2ch 48000Hz RUNNING",
            "0 alsa_input.pci-1.analog-stereo module-alsa-card.c s16le 2ch 48000Hz RUNNING\n1 alsa_output.pci-1.monitor module-alsa-card.c s16le 2ch 48000Hz RUNNING",
        ])
        with patch.object(hardware, "_run", side_effect=lambda *_args, **_kwargs: next(responses)):
            self.assertEqual(
                hardware._audio_details(),
                ("PipeWire / PulseAudio", "alsa_output.pci-1.analog-stereo", "1 entrée(s) détectée(s)"),
            )

    def test_audio_inventory_ignores_malformed_source_rows(self):
        responses = iter([
            "Server Name: PipeWire\nDefault Sink: output.test",
            "",
            "malformed-source-row\n0 input.test module-test s16le 2ch 48000Hz RUNNING",
        ])
        with patch.object(hardware, "_run", side_effect=lambda *_args, **_kwargs: next(responses)):
            self.assertEqual(
                hardware._audio_details(),
                ("PipeWire / PulseAudio", "output.test", "1 entrée(s) détectée(s)"),
            )

    def test_network_summary_omits_loopback_and_keeps_local_addresses(self):
        with patch.object(
            hardware, "_run",
            return_value="lo UNKNOWN 127.0.0.1/8\nenp4s0 UP 192.168.1.20/24 fe80::1/64\nwlan0 DOWN",
        ):
            self.assertEqual(
                hardware._network_details(),
                "enp4s0 · up · 192.168.1.20/24, fe80::1/64 | wlan0 · down · Aucune adresse IP",
            )

    def test_network_summary_handles_missing_ip_tool(self):
        with patch.object(hardware, "_run", return_value=""):
            self.assertEqual(hardware._network_details(), "État réseau indisponible")

    def test_battery_and_usb_are_reported_as_absent_when_sysfs_has_none(self):
        with patch.object(hardware.Path, "glob", return_value=[]):
            self.assertEqual(hardware._battery_details(), "Aucune batterie détectée")
            self.assertEqual(hardware._usb_details(), "Aucun périphérique USB listé")

    def test_subprocess_invalid_output_encoding_is_non_fatal(self):
        error = UnicodeDecodeError("utf-8", b"\\xff", 0, 1, "invalid byte")
        with patch.object(hardware.subprocess, "run", side_effect=error):
            self.assertEqual(hardware._run(["kscreen-doctor", "-o"]), "")

    def test_subprocess_timeout_and_missing_commands_are_non_fatal(self):
        with patch.object(hardware.subprocess, "run", side_effect=FileNotFoundError):
            self.assertEqual(hardware._run(["bluetoothctl"]), "")
        with patch.object(hardware.subprocess, "run", side_effect=hardware.subprocess.TimeoutExpired("pactl", 1)):
            self.assertEqual(hardware._run(["pactl"]), "")


if __name__ == "__main__":
    unittest.main()
