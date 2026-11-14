"""Tests for PCI-matched GPU telemetry on hybrid and multi-GPU systems."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from gaming.backend import gpu_metrics


class GpuMetricsTests(unittest.TestCase):
    def _add_drm_gpu(self, root: Path, card: str, pci: str, vendor: str, device_id: str) -> None:
        target = root / "devices" / "pci0000:00" / pci
        target.mkdir(parents=True)
        (target / "vendor").write_text(vendor, encoding="ascii")
        (target / "device").write_text(device_id, encoding="ascii")
        drm = root / "class" / "drm"
        drm.mkdir(parents=True, exist_ok=True)
        (drm / card).mkdir()
        (drm / card / "device").symlink_to(target)

    def test_normalizes_linux_and_nvidia_smi_pci_addresses(self):
        self.assertEqual(
            gpu_metrics._normalize_pci_address("0000:01:00.0"),
            "0000:01:00.0",
        )
        self.assertEqual(
            gpu_metrics._normalize_pci_address("00000000:01:00.0"),
            "0000:01:00.0",
        )
        self.assertEqual(
            gpu_metrics._normalize_pci_address("00000001:0A:1f.1"),
            "0001:0a:1f.1",
        )
        self.assertIsNone(gpu_metrics._normalize_pci_address("not-a-pci-address"))
        self.assertIsNone(gpu_metrics._normalize_pci_address("100000000:01:00.0"))

    def test_resolves_pci_identity_from_drm_device_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._add_drm_gpu(root, "card0", "0000:03:00.0", "0x10de", "0x2484")
            self.assertEqual(
                gpu_metrics._pci_address_for_device(root / "class/drm/card0/device"),
                "0000:03:00.0",
            )

    def test_nvidia_rows_are_matched_by_pci_not_command_output_order(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "sys"
            self._add_drm_gpu(root, "card0", "0000:01:00.0", "0x10de", "0x1111")
            self._add_drm_gpu(root, "card1", "0000:02:00.0", "0x10de", "0x2222")
            # Deliberately report card1 first: nvidia-smi output order must not
            # be assumed to match DRM card numbering.
            output = (
                "00000000:02:00.0, NVIDIA GPU B, 88, 82, 300, 8000\n"
                "00000000:01:00.0, NVIDIA GPU A, 20, 42, 500, 4000\n"
            )
            completed = SimpleNamespace(returncode=0, stdout=output)
            with patch.object(gpu_metrics.shutil, "which", return_value="/usr/bin/nvidia-smi"):
                with patch.object(gpu_metrics.subprocess, "run", return_value=completed):
                    metrics = gpu_metrics.read_gpu_metrics(root)

        self.assertEqual(metrics["name"], "NVIDIA GPU A")
        self.assertEqual(metrics["usage"], 20.0)
        self.assertEqual(metrics["temperature"], 42.0)
        self.assertEqual(metrics["memory_used"], 500 * 1024 * 1024)
        self.assertEqual(metrics["memory_total"], 4000 * 1024 * 1024)

    def test_does_not_apply_nvidia_telemetry_to_a_different_pci_device(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "sys"
            self._add_drm_gpu(root, "card0", "0000:01:00.0", "0x10de", "0x1111")
            output = "00000000:02:00.0, Unrelated NVIDIA GPU, 88, 82, 300, 8000\n"
            completed = SimpleNamespace(returncode=0, stdout=output)
            with patch.object(gpu_metrics.shutil, "which", return_value="/usr/bin/nvidia-smi"):
                with patch.object(gpu_metrics.subprocess, "run", return_value=completed):
                    metrics = gpu_metrics.read_gpu_metrics(root)

        self.assertEqual(metrics["name"], "NVIDIA · PCI 0x1111")
        self.assertEqual(metrics["usage"], -1.0)
        self.assertEqual(metrics["temperature"], -1.0)
        self.assertEqual(metrics["memory_used"], -1)
        self.assertEqual(metrics["memory_total"], -1)

    def test_missing_nvidia_smi_and_missing_drm_return_unavailable_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(gpu_metrics.shutil, "which", return_value=None):
                metrics = gpu_metrics.read_gpu_metrics(Path(temporary) / "empty")
        self.assertEqual(metrics, {
            "name": "GPU non détecté",
            "usage": -1.0,
            "temperature": -1.0,
            "memory_used": -1,
            "memory_total": -1,
        })

    def test_nvidia_fallback_selects_a_complete_record_without_drm_nodes(self):
        output = (
            "00000000:02:00.0, NVIDIA GPU B, N/A, N/A, N/A, N/A\n"
            "00000000:01:00.0, NVIDIA GPU A, 45, 61, 1024, 8192\n"
        )
        completed = SimpleNamespace(returncode=0, stdout=output)
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(gpu_metrics.shutil, "which", return_value="/usr/bin/nvidia-smi"):
                with patch.object(gpu_metrics.subprocess, "run", return_value=completed):
                    metrics = gpu_metrics.read_gpu_metrics(Path(temporary) / "empty")
        self.assertEqual(metrics["name"], "NVIDIA GPU A")
        self.assertEqual(metrics["usage"], 45.0)
        self.assertEqual(metrics["temperature"], 61.0)

    def test_gpu_metrics_normalizer_rejects_stale_or_invalid_values(self):
        normalized = gpu_metrics.normalize_gpu_metrics({
            "name": "  Radeon test  ",
            "usage": float("nan"),
            "temperature": 999,
            "memory_used": 9000,
            "memory_total": 8000,
        })
        self.assertEqual(normalized, {
            "name": "Radeon test",
            "usage": -1.0,
            "temperature": -1.0,
            "memory_used": -1,
            "memory_total": 8000,
        })

    def test_gpu_metrics_normalizer_handles_missing_and_non_numeric_values(self):
        self.assertEqual(
            gpu_metrics.normalize_gpu_metrics({"name": "", "usage": "broken"}),
            gpu_metrics.unavailable_gpu_metrics(),
        )
        self.assertEqual(
            gpu_metrics.normalize_gpu_metrics(None),
            gpu_metrics.unavailable_gpu_metrics(),
        )

    def test_gpu_metrics_normalizer_keeps_valid_zero_usage_and_memory(self):
        self.assertEqual(
            gpu_metrics.normalize_gpu_metrics({
                "name": "Intel Graphics",
                "usage": 0,
                "temperature": 42.5,
                "memory_used": 0,
                "memory_total": 4096,
            }),
            {
                "name": "Intel Graphics",
                "usage": 0.0,
                "temperature": 42.5,
                "memory_used": 0,
                "memory_total": 4096,
            },
        )

    def test_nvidia_smi_invalid_text_encoding_is_non_fatal(self):
        invalid_text = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid byte")
        with patch.object(gpu_metrics.shutil, "which", return_value="/usr/bin/nvidia-smi"):
            with patch.object(gpu_metrics.subprocess, "run", side_effect=invalid_text):
                self.assertEqual(gpu_metrics._nvidia_smi_devices(), {})

    def test_nvidia_smi_timeout_is_non_fatal(self):
        with patch.object(gpu_metrics.shutil, "which", return_value="/usr/bin/nvidia-smi"):
            with patch.object(
                gpu_metrics.subprocess,
                "run",
                side_effect=gpu_metrics.subprocess.TimeoutExpired("nvidia-smi", 2.0),
            ):
                self.assertEqual(gpu_metrics._nvidia_smi_devices(), {})


if __name__ == "__main__":
    unittest.main()
