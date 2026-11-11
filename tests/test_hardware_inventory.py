"""Tests for the read-only hardware inventory."""
import unittest
from unittest.mock import patch

from control_center import hardware


class HardwareInventoryTests(unittest.TestCase):
    def test_snapshot_exposes_all_dashboard_fields(self):
        snapshot = hardware.collect_hardware_snapshot()
        expected = {
            "cpu", "cpuThreads", "memory", "storage", "gpu",
            "operatingSystem", "kernel", "bluetooth", "bluetoothDevices",
            "audioServer", "audioOutput", "audioInputs", "controllers", "battery", "usbDevices", "network",
        }
        self.assertEqual(set(snapshot), expected)
        self.assertTrue(all(isinstance(value, str) for value in snapshot.values()))

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
