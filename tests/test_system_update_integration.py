"""Structural tests for the Control Center system update page."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SystemUpdateIntegrationTests(unittest.TestCase):
    def test_control_center_exposes_check_and_native_updater_actions(self):
        controller = (ROOT / "control_center/controller.py").read_text(encoding="utf-8")
        qml = (ROOT / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("def checkForSystemUpdates", controller)
        self.assertIn("def openSystemUpdater", controller)
        update_module = (ROOT / "control_center/system_updates.py").read_text(encoding="utf-8")
        self.assertIn('"update-check"', update_module)
        self.assertIn("controlCenter.checkForSystemUpdates()", qml)
        self.assertIn("controlCenter.openSystemUpdater()", qml)
        self.assertIn("Mises à jour", qml)
        self.assertIn("refreshPendingSystemUpdate", controller)
        self.assertIn("setInterval(10 * 60 * 1000)", controller)
        self.assertIn('"status", "--json"', update_module)
        self.assertIn("pending_deployment_from_status", update_module)

    def test_system_update_probes_have_bounded_runtime(self):
        controller = (ROOT / "control_center/controller.py").read_text(encoding="utf-8")
        self.assertIn("SYSTEM_UPDATE_CHECK_TIMEOUT_MS = 120_000", controller)
        self.assertIn("DEPLOYMENT_STATUS_TIMEOUT_MS = 20_000", controller)
        self.assertIn("self._system_update_timeout.setSingleShot(True)", controller)
        self.assertIn("self._system_update_timeout.timeout.connect(self._on_system_update_check_timeout)", controller)
        self.assertIn("self._deployment_timeout.setSingleShot(True)", controller)
        self.assertIn("self._deployment_timeout.timeout.connect(self._on_deployment_status_timeout)", controller)
        self.assertIn("self._system_update_process.kill()", controller)
        self.assertIn("self._deployment_process.kill()", controller)
        self.assertIn("a dépassé deux minutes", controller)
        self.assertIn("if self._system_update_timed_out:", controller)
        self.assertIn("if self._deployment_timed_out:", controller)

    def test_update_check_never_calls_install_or_upgrade(self):
        module = (ROOT / "control_center/system_updates.py").read_text(encoding="utf-8")
        controller = (ROOT / "control_center/controller.py").read_text(encoding="utf-8")
        self.assertIn('"update-check"', module)
        self.assertNotIn('"update"', module)
        self.assertNotIn('"upgrade"', module)
        self.assertNotIn("uupd-update", controller)
        self.assertNotIn('"upgrade"', module)
        self.assertNotIn('"deploy"', module)

    def test_update_installation_remains_user_controlled(self):
        qml = (ROOT / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("OUVRIR BAZZITE UPDATER", qml)
        self.assertIn("sans lancer de téléchargement ni d’installation", qml)
        self.assertIn('{ label: "Mises à jour", page: 5 }', qml)


if __name__ == "__main__":
    unittest.main()
