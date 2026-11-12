"""Structural tests for the Control Center diagnostics page."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SystemDiagnosticsIntegrationTests(unittest.TestCase):
    def test_diagnostics_are_exposed_and_refreshed_off_the_ui_thread(self):
        controller = (ROOT / "control_center/controller.py").read_text(encoding="utf-8")
        qml = (ROOT / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("def diagnosticsSnapshot", controller)
        self.assertIn("def scanDiagnostics", controller)
        self.assertIn("QThreadPool.globalInstance().start(task)", controller)
        self.assertIn("setInterval(30_000)", controller)
        self.assertIn('{ label: "Diagnostic système", page: 7 }', qml)
        self.assertIn("controlCenter.diagnosticsSnapshot.findings", qml)
        self.assertIn("controlCenter.scanDiagnostics()", qml)
        self.assertIn("controlCenter.diagnosticsSnapshot.topProcesses", qml)
        self.assertIn("controlCenter.openSystemMonitor()", qml)
        self.assertIn("def openSystemMonitor", controller)

    def test_background_scans_always_release_their_controller_task_slot(self):
        controller = (ROOT / "control_center/controller.py").read_text(encoding="utf-8")
        for task in (
            "_HardwareScanTask",
            "_NetworkScanTask",
            "_DiagnosticsScanTask",
            "_CleanupScanTask",
        ):
            start = controller.index(f"class {task}")
            end = controller.find("\\nclass ", start + 1)
            block = controller[start:end if end >= 0 else len(controller)]
            self.assertIn("except Exception:", block)
            self.assertIn('{"_scan_error":', block)
        for handler in (
            "_on_hardware_scan_completed",
            "_on_network_scan_completed",
            "_on_diagnostics_completed",
            "_on_cleanup_preview_completed",
        ):
            start = controller.index(f"def {handler}")
            block = controller[start:start + 500]
            self.assertIn('snapshot.get("_scan_error")', block)

    def test_diagnostics_module_does_not_define_repair_or_restart_actions(self):
        module = (ROOT / "control_center/diagnostics.py").read_text(encoding="utf-8")
        for forbidden in ('["restart"', '["start"', '["stop"', '["repair"', '"rpm-ostree", "upgrade"'):
            self.assertNotIn(forbidden, module)
        self.assertIn('"--failed"', module)
        self.assertIn('"--priority=err"', module)
        self.assertIn('shutil.disk_usage("/")', module)


if __name__ == "__main__":
    unittest.main()
