"""Tests for read-only LEOS system diagnostics."""
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from control_center import diagnostics


class SystemDiagnosticsTests(unittest.TestCase):
    def test_failed_services_are_extracted_without_running_repairs(self):
        with patch.object(
            diagnostics, "_run",
            return_value="cups.service loaded failed failed CUPS Scheduler\nsshd.service loaded active running OpenSSH",
        ):
            summary, names = diagnostics._failed_services()
        self.assertEqual(summary, "1 unité(s) en échec")
        self.assertEqual(names, ["cups.service"])

    def test_memory_percentage_uses_available_memory(self):
        data = "MemTotal: 1000 kB\nMemAvailable: 250 kB\n"
        with patch.object(diagnostics, "_read", return_value=data):
            self.assertEqual(diagnostics._memory_percent(), 75.0)

    def test_temperature_handles_millidegrees_and_invalid_sensors(self):
        values = {
            "/sys/class/thermal/thermal_zone0/temp": "42000",
            "/sys/class/thermal/thermal_zone0/type": "cpu-thermal",
            "/sys/class/thermal/thermal_zone1/temp": "bad",
            "/sys/class/thermal/thermal_zone1/type": "unknown",
        }
        with (
            patch.object(diagnostics.Path, "glob", return_value=[diagnostics.Path(k) for k in values]),
            patch.object(diagnostics, "_read", side_effect=lambda path: values.get(str(path), "")),
        ):
            self.assertEqual(diagnostics._temperature_celsius(), 42.0)

    def test_temperature_uses_chip_name_when_sensor_label_is_generic(self):
        sensor = diagnostics.Path("/sys/class/hwmon/hwmon0/temp1_input")
        values = {
            str(sensor): "68000",
            str(sensor.with_name("temp1_label")): "temp1",
            str(sensor.parent / "name"): "k10temp",
        }
        with (
            patch.object(diagnostics.Path, "glob", side_effect=[[sensor], []]),
            patch.object(diagnostics, "_read", side_effect=lambda path: values.get(str(path), "")),
        ):
            self.assertEqual(diagnostics._temperature_celsius(), 68.0)

    def test_temperature_does_not_mislabel_unknown_thermal_zone_as_cpu(self):
        path = diagnostics.Path("/sys/class/thermal/thermal_zone0/temp")
        values = {
            str(path): "99000",
            str(path.parent / "type"): "wifi-radio",
        }
        with (
            patch.object(diagnostics.Path, "glob", side_effect=[[], [path]]),
            patch.object(diagnostics, "_read", side_effect=lambda item: values.get(str(item), "")),
        ):
            self.assertIsNone(diagnostics._temperature_celsius())

    def test_temperature_prefers_labelled_cpu_sensor_over_unrelated_hot_zone(self):
        hwmon_inputs = [
            diagnostics.Path("/sys/class/hwmon/hwmon0/temp1_input"),
            diagnostics.Path("/sys/class/hwmon/hwmon0/temp2_input"),
        ]
        thermal_inputs = [
            diagnostics.Path("/sys/class/thermal/thermal_zone0/temp"),
            diagnostics.Path("/sys/class/thermal/thermal_zone1/temp"),
        ]

        values = {
            str(hwmon_inputs[0]): "76000",
            str(hwmon_inputs[0].with_name("temp1_label")): "Package id 0",
            str(hwmon_inputs[0].parent / "name"): "coretemp",
            str(hwmon_inputs[1]): "99000",
            str(hwmon_inputs[1].with_name("temp2_label")): "Ambient",
            str(thermal_inputs[0]): "93000",
            str(thermal_inputs[0].parent / "type"): "acpitz",
            str(thermal_inputs[1]): "82000",
            str(thermal_inputs[1].parent / "type"): "cpu-thermal",
        }
        with (
            patch.object(diagnostics.Path, "glob", side_effect=[hwmon_inputs, thermal_inputs]),
            patch.object(diagnostics, "_read", side_effect=lambda path: values.get(str(path), "")),
        ):
            self.assertEqual(diagnostics._temperature_celsius(), 76.0)

    def test_uptime_formats_days_and_handles_missing_file(self):
        with patch.object(diagnostics, "_read", return_value="176461.0 123456.0"):
            self.assertEqual(diagnostics._uptime(), "2 j 1 h")
        with patch.object(diagnostics, "_read", return_value=""):
            self.assertEqual(diagnostics._uptime(), "Indisponible")

    def test_critical_disk_space_produces_actionable_finding(self):
        usage = SimpleNamespace(used=95, total=100, free=5)
        with (
            patch.object(diagnostics.shutil, "disk_usage", return_value=usage),
            patch.object(diagnostics, "_memory_percent", return_value=30.0),
            patch.object(diagnostics, "_temperature_celsius", return_value=45.0),
            patch.object(diagnostics, "_failed_services", return_value=("Aucune unité en échec", [])),
            patch.object(diagnostics, "_recent_error_count", return_value="0 entrée(s) d'erreur récente(s)"),
            patch.object(diagnostics, "_uptime", return_value="1 h"),
            patch.object(diagnostics.os, "getloadavg", return_value=(0.1, 0.2, 0.3)),
            patch.object(diagnostics.os, "cpu_count", return_value=4),
        ):
            result = diagnostics.collect_system_diagnostics()
        self.assertEqual(result["severity"], "Critique")
        self.assertIn("Espace disque critique", result["findings"][0])

    def test_healthy_report_does_not_invent_anomalies(self):
        usage = SimpleNamespace(used=40, total=100, free=60)
        with (
            patch.object(diagnostics.shutil, "disk_usage", return_value=usage),
            patch.object(diagnostics, "_memory_percent", return_value=40.0),
            patch.object(diagnostics, "_temperature_celsius", return_value=50.0),
            patch.object(diagnostics, "_failed_services", return_value=("Aucune unité en échec", [])),
            patch.object(diagnostics, "_recent_error_count", return_value="0 entrée(s) d'erreur récente(s)"),
            patch.object(diagnostics, "_uptime", return_value="2 h"),
            patch.object(diagnostics.os, "getloadavg", return_value=(0.1, 0.2, 0.3)),
            patch.object(diagnostics.os, "cpu_count", return_value=4),
        ):
            result = diagnostics.collect_system_diagnostics()
        self.assertEqual(result["severity"], "OK")
        self.assertEqual(result["findings"], ["Aucune anomalie détectée par les contrôles disponibles."])

    def test_top_processes_are_parsed_and_limited_to_eight(self):
        rows = [
            f"{pid} process{pid} 12.5 3.2 2048"
            for pid in range(1, 11)
        ]
        with patch.object(diagnostics, "_run", return_value="\n".join(rows)):
            result = diagnostics._top_processes()
        self.assertEqual(len(result), 8)
        self.assertEqual(result[0], {
            "pid": "1", "name": "process1", "cpu": "12.5%",
            "memory": "3.2%", "resident": "2 Mio",
        })

    def test_missing_commands_and_timeouts_are_safe(self):
        with patch.object(diagnostics.subprocess, "run", side_effect=FileNotFoundError):
            self.assertEqual(diagnostics._run(["systemctl"]), "")
        with patch.object(
            diagnostics.subprocess, "run",
            side_effect=diagnostics.subprocess.TimeoutExpired("journalctl", 1),
        ):
            self.assertEqual(diagnostics._run(["journalctl"]), "")


if __name__ == "__main__":
    unittest.main()
