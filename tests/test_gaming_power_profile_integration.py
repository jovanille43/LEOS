"""Structural checks for the Gaming power profile controls."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class GamingPowerProfileIntegrationTests(unittest.TestCase):
    def test_controller_exposes_native_profiles_and_refreshes_external_changes(self):
        controller = (ROOT / "gaming/backend/controller.py").read_text(encoding="utf-8")
        self.assertIn("def activePowerProfile", controller)
        self.assertIn("def availablePowerProfiles", controller)
        self.assertIn("def refreshPowerProfiles", controller)
        self.assertIn("def applyPowerProfile", controller)
        self.assertIn("setInterval(10000)", controller)

    def test_qml_requires_confirmation_before_applying_profile(self):
        qml = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("powerProfileDialog.open()", qml)
        self.assertIn('title: "Confirmer le profil d’énergie"', qml)
        self.assertIn("leos.applyPowerProfile(window.pendingPowerProfile)", qml)
        self.assertIn("powerProfileStatus", qml)

    def test_profile_backend_uses_only_native_powerprofilesctl(self):
        module = (ROOT / "gaming/backend/power_profiles.py").read_text(encoding="utf-8")
        self.assertIn('["get"]', module)
        self.assertIn('["list"]', module)
        self.assertIn('"set", profile', module)
        self.assertNotIn("fancontrol", module)
        self.assertNotIn("sysfs", module)


if __name__ == "__main__":
    unittest.main()
