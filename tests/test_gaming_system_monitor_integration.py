"""Structural checks for Gaming telemetry availability and resilience."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class GamingSystemMonitorIntegrationTests(unittest.TestCase):
    def test_gpu_collection_is_independent_of_psutil(self):
        source = (ROOT / "gaming/backend/system_monitor.py").read_text(encoding="utf-8")
        refresh = source.split("    def refresh(self) -> None:", 1)[1].split(
            "    @Property", 1
        )[0]
        self.assertLess(refresh.index("if psutil is not None:"), refresh.index("gpu = read_gpu_metrics()"))
        self.assertIn("self.metricsChanged.emit()", refresh)

    def test_monitor_availability_includes_gpu_only_hosts(self):
        source = (ROOT / "gaming/backend/system_monitor.py").read_text(encoding="utf-8")
        self.assertIn("return psutil is not None or self._gpu_name != \"GPU non détecté\"", source)
        self.assertIn("@Property(bool, notify=metricsChanged)", source)


if __name__ == "__main__":
    unittest.main()
