"""Tests for best-effort GPU telemetry exposed by Gaming Mode."""

import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from gaming.backend.gpu_metrics import read_gpu_metrics


class GpuTelemetryTests(unittest.TestCase):
    def test_reads_supported_drm_metrics_without_guessing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            device = root / "class" / "drm" / "card0" / "device"
            device.mkdir(parents=True)
            (device / "vendor").write_text("0x1002")
            (device / "device").write_text("0x164e")
            (device / "gpu_busy_percent").write_text("47")
            (device / "mem_info_vram_used").write_text("536870912")
            (device / "mem_info_vram_total").write_text("2147483648")

            metrics = read_gpu_metrics(root)

        self.assertEqual(metrics["name"], "AMD · PCI 0x164e")
        self.assertEqual(metrics["usage"], 47.0)
        self.assertEqual(metrics["temperature"], -1.0)
        self.assertEqual(metrics["memory_used"], 536870912)
        self.assertEqual(metrics["memory_total"], 2147483648)

    def test_hybrid_system_prefers_gpu_with_available_discrete_telemetry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            integrated = root / "class" / "drm" / "card0" / "device"
            discrete = root / "class" / "drm" / "card10" / "device"
            connector = root / "class" / "drm" / "card10-DP-1" / "device"
            for device in (integrated, discrete, connector):
                device.mkdir(parents=True)
            (integrated / "vendor").write_text("0x8086")
            (integrated / "device").write_text("0x4680")
            (integrated / "gpu_busy_percent").write_text("22")
            (discrete / "vendor").write_text("0x10de")
            (discrete / "device").write_text("0x2684")
            (discrete / "gpu_busy_percent").write_text("78")
            (discrete / "mem_info_vram_used").write_text("2147483648")
            (discrete / "mem_info_vram_total").write_text("8589934592")
            (connector / "vendor").write_text("0x1002")
            (connector / "device").write_text("0x164e")
            (connector / "gpu_busy_percent").write_text("99")

            metrics = read_gpu_metrics(root)

        self.assertEqual(metrics["name"], "NVIDIA · PCI 0x2684")
        self.assertEqual(metrics["usage"], 78.0)
        self.assertEqual(metrics["memory_used"], 2147483648)
        self.assertEqual(metrics["memory_total"], 8589934592)

    def test_missing_gpu_or_driver_metrics_remain_unavailable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metrics = read_gpu_metrics(root)
        self.assertEqual(metrics["name"], "GPU non détecté")
        self.assertEqual(metrics["usage"], -1.0)
        self.assertEqual(metrics["temperature"], -1.0)
        self.assertEqual(metrics["memory_used"], -1)
        self.assertEqual(metrics["memory_total"], -1)


    def test_reads_gpu_temperature_only_from_gpu_associated_hwmon(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            device = root / "class" / "drm" / "card0" / "device"
            sensor = device / "hwmon" / "hwmon0"
            sensor.mkdir(parents=True)
            (device / "vendor").write_text("0x1002")
            (device / "device").write_text("0x164e")
            (sensor / "temp1_label").write_text("edge")
            (sensor / "temp1_input").write_text("62500")
            (sensor / "temp2_label").write_text("junction")
            (sensor / "temp2_input").write_text("85000")
            metrics = read_gpu_metrics(root)
        self.assertEqual(metrics["temperature"], 62.5)

    @patch("gaming.backend.gpu_metrics.shutil.which", return_value="/usr/bin/nvidia-smi")
    @patch("gaming.backend.gpu_metrics.subprocess.run")
    def test_uses_nvidia_smi_when_no_drm_gpu_is_exposed(self, run, _which):
        run.return_value.returncode = 0
        run.return_value.stdout = "00000000:01:00.0, NVIDIA GeForce RTX 4070, 63, 68, 4096, 12288\n"
        with tempfile.TemporaryDirectory() as temporary:
            metrics = read_gpu_metrics(Path(temporary))
        self.assertEqual(metrics["name"], "NVIDIA GeForce RTX 4070")
        self.assertEqual(metrics["usage"], 63.0)
        self.assertEqual(metrics["temperature"], 68.0)
        self.assertEqual(metrics["memory_used"], 4096 * 1024 * 1024)
        self.assertEqual(metrics["memory_total"], 12288 * 1024 * 1024)
        self.assertIn("pci.bus_id,name", run.call_args.args[0][1])
        self.assertEqual(run.call_args.kwargs["timeout"], 2.0)

    @patch("gaming.backend.gpu_metrics.shutil.which", return_value=None)
    def test_nvidia_fallback_is_optional(self, _which):
        with tempfile.TemporaryDirectory() as temporary:
            metrics = read_gpu_metrics(Path(temporary))
        self.assertEqual(metrics["name"], "GPU non détecté")

    @patch("gaming.backend.gpu_metrics.shutil.which", return_value="/usr/bin/nvidia-smi")
    @patch("gaming.backend.gpu_metrics.subprocess.run")
    def test_nvidia_fallback_ignores_unavailable_and_out_of_range_values(self, run, _which):
        run.return_value.returncode = 0
        run.return_value.stdout = "00000000:01:00.0, NVIDIA GPU, N/A, 190, N/A, 8192\n"
        with tempfile.TemporaryDirectory() as temporary:
            metrics = read_gpu_metrics(Path(temporary))
        self.assertEqual(metrics["usage"], -1.0)
        self.assertEqual(metrics["temperature"], -1.0)
        self.assertEqual(metrics["memory_used"], -1)
        self.assertEqual(metrics["memory_total"], 8192 * 1024 * 1024)

    def test_invalid_usage_is_not_exposed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            device = root / "class" / "drm" / "card0" / "device"
            device.mkdir(parents=True)
            (device / "vendor").write_text("0x10de")
            (device / "device").write_text("0x2684")
            (device / "gpu_busy_percent").write_text("140")
            metrics = read_gpu_metrics(root)
        self.assertEqual(metrics["usage"], -1.0)
        self.assertEqual(metrics["name"], "NVIDIA · PCI 0x2684")


if __name__ == "__main__":
    unittest.main()
