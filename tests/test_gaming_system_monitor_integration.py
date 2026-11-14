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
        self.assertLess(
            refresh.index("if psutil is not None:"),
            refresh.index("gpu = normalize_gpu_metrics(read_gpu_metrics())"),
        )
        self.assertIn("self.metricsChanged.emit()", refresh)

    def test_gpu_provider_failure_clears_previous_metrics_instead_of_reusing_them(self):
        source = (ROOT / "gaming/backend/system_monitor.py").read_text(encoding="utf-8")
        refresh = source.split("    def refresh(self) -> None:", 1)[1].split(
            "    @Property", 1
        )[0]
        self.assertIn("except Exception:", refresh)
        self.assertIn("gpu = unavailable_gpu_metrics()", refresh)
        self.assertIn("self._gpu_usage = float(gpu[\"usage\"])", refresh)

    def test_each_psutil_metric_has_an_independent_error_boundary(self):
        import ast

        source = (ROOT / "gaming/backend/system_monitor.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        monitor = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "SystemMonitor"
        )
        refresh = next(
            node for node in monitor.body
            if isinstance(node, ast.FunctionDef) and node.name == "refresh"
        )
        protected_calls = set()
        for node in ast.walk(refresh):
            if not isinstance(node, ast.Try):
                continue
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    func = child.func
                    if isinstance(func, ast.Attribute):
                        protected_calls.add(func.attr)
        self.assertTrue({
            "cpu_percent", "virtual_memory", "_read_cpu_temperature",
            "_read_disk_usage", "_read_network_rates",
        }.issubset(protected_calls))

    def test_cpu_temperature_uses_highest_valid_value_from_cpu_sensors(self):
        source = (ROOT / "gaming/backend/system_monitor.py").read_text(encoding="utf-8")
        self.assertIn("return max(readings) if readings else -1.0", source)
        self.assertIn("if 0 < current < 150:", source)

    def test_monitor_availability_includes_gpu_only_hosts(self):
        source = (ROOT / "gaming/backend/system_monitor.py").read_text(encoding="utf-8")
        self.assertIn("return psutil is not None or self._gpu_name != \"GPU non détecté\"", source)
        self.assertIn("@Property(bool, notify=metricsChanged)", source)


if __name__ == "__main__":
    unittest.main()
