"""Structural tests for the LEOS network dashboard."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class NetworkDashboardIntegrationTests(unittest.TestCase):
    def test_network_snapshot_is_sampled_off_the_ui_thread(self):
        controller = (ROOT / "control_center/controller.py").read_text(encoding="utf-8")
        qml = (ROOT / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("def networkSnapshot", controller)
        self.assertIn("def scanNetwork", controller)
        self.assertIn("_NetworkScanTask", controller)
        self.assertIn("QThreadPool.globalInstance().start(task)", controller)
        self.assertIn("setInterval(3000)", controller)
        self.assertIn("networkChanged = Signal()", controller)
        self.assertIn('{ label: "Réseau", page: 9 }', qml)
        self.assertIn("controlCenter.networkSnapshot.interfaces", qml)
        self.assertIn("controlCenter.scanNetwork()", qml)

    def test_network_module_is_read_only_and_does_not_probe_external_hosts(self):
        module = (ROOT / "control_center/network.py").read_text(encoding="utf-8")
        self.assertIn("/sys/class/net", module)
        self.assertIn("/proc/net/route", module)
        self.assertIn("/etc/resolv.conf", module)
        self.assertNotIn("ping", module)
        self.assertNotIn("iperf", module)
        self.assertNotIn("nmcli connection modify", module)


if __name__ == "__main__":
    unittest.main()
