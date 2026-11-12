"""Tests for resilient Gaming Mode system telemetry."""

import unittest
from unittest.mock import patch

from gaming.backend.system_monitor import SystemMonitor


class SystemMonitorTests(unittest.TestCase):
    @patch("gaming.backend.system_monitor.psutil", None)
    @patch("gaming.backend.system_monitor.read_gpu_metrics")
    def test_gpu_metrics_refresh_when_psutil_is_unavailable(self, read_gpu):
        read_gpu.return_value = {
            "name": "NVIDIA GeForce RTX 4070",
            "usage": 63.0,
            "temperature": 68.0,
            "memory_used": 4 * 1024**3,
            "memory_total": 12 * 1024**3,
        }
        monitor = SystemMonitor()
        monitor.refresh()
        self.assertEqual(monitor.gpuName, "NVIDIA GeForce RTX 4070")
        self.assertEqual(monitor.gpuUsage, 63.0)
        self.assertEqual(monitor.gpuTemperature, 68.0)
        self.assertEqual(monitor.gpuMemoryUsed, 4 * 1024**3)
        self.assertEqual(monitor.gpuMemoryTotal, 12 * 1024**3)
        read_gpu.assert_called_once_with()

    @patch("gaming.backend.system_monitor.psutil")
    @patch("gaming.backend.system_monitor.read_gpu_metrics")
    def test_gpu_metrics_refresh_even_if_cpu_metrics_raise(self, read_gpu, psutil):
        psutil.cpu_percent.side_effect = OSError("CPU counters unavailable")
        read_gpu.return_value = {
            "name": "AMD Radeon",
            "usage": 31.0,
            "temperature": -1.0,
            "memory_used": -1,
            "memory_total": -1,
        }
        monitor = SystemMonitor()
        monitor.refresh()
        self.assertEqual(monitor.gpuName, "AMD Radeon")
        self.assertEqual(monitor.gpuUsage, 31.0)

    @patch("gaming.backend.system_monitor.read_gpu_metrics", side_effect=KeyError("usage"))
    def test_malformed_gpu_snapshot_does_not_crash_refresh(self, _read_gpu):
        monitor = SystemMonitor()
        monitor.refresh()
        self.assertEqual(monitor.gpuName, "GPU non détecté")


if __name__ == "__main__":
    unittest.main()
