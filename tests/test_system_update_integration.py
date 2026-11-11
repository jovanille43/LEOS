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
        self.assertIn("uupd update-check", controller)
        self.assertIn("controlCenter.checkForSystemUpdates()", qml)
        self.assertIn("controlCenter.openSystemUpdater()", qml)
        self.assertIn("Mises à jour", qml)

    def test_update_check_never_calls_install_or_upgrade(self):
        module = (ROOT / "control_center/system_updates.py").read_text(encoding="utf-8")
        controller = (ROOT / "control_center/controller.py").read_text(encoding="utf-8")
        self.assertIn('"update-check"', module)
        self.assertNotIn('"update"', module)
        self.assertNotIn('"upgrade"', module)
        self.assertNotIn("uupd-update", controller)

    def test_update_installation_remains_user_controlled(self):
        qml = (ROOT / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("Ouvre Bazzite Updater", qml)
        self.assertIn("aucune mise à jour n'est installée par cette vérification", qml)


if __name__ == "__main__":
    unittest.main()
