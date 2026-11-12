"""Tests for the read-only hardware inventory."""

import unittest
import tempfile
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
            stream.write(b"Model: Test CPU\\xff")
            stream.flush()
            self.assertEqual(hardware._read(stream.name), "Model: Test CPU\\ufffd")

    def test_snapshot_exposes_all_dashboard_fields(self):
        snapshot = hardware.collect_hardware_snapshot()
        expected = {
            "cpu", "cpuThreads", "cpuCores", "memory", "storage", "gpu", "vulkan",
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

    def test_subprocess_timeout_and_missing_commands_are_non_fatal(self):
        with patch.object(hardware.subprocess, "run", side_effect=FileNotFoundError):
            self.assertEqual(hardware._run(["bluetoothctl"]), "")
        with patch.object(hardware.subprocess, "run", side_effect=hardware.subprocess.TimeoutExpired("pactl", 1)):
            self.assertEqual(hardware._run(["pactl"]), "")


if __name__ == "__main__":
    unittest.main()
