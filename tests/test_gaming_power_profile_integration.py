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

    def test_power_profile_queries_and_changes_run_off_the_qml_thread(self):
        controller = (ROOT / "gaming/backend/controller.py").read_text(encoding="utf-8")
        class_start = controller.index("class GamingController")
        constructor_start = controller.index("def __init__", class_start)
        constructor_end = controller.index("@Property(bool", constructor_start)
        constructor = controller[constructor_start:constructor_end]
        self.assertNotIn("inspect_power_profiles()", constructor)
        self.assertIn("class _PowerProfileTask(QRunnable)", controller)
        self.assertIn("QThreadPool.globalInstance().start(task)", controller)
        refresh = controller[controller.index("def refreshPowerProfiles"):controller.index("@Property(str, notify=launchStatusChanged)")]
        self.assertNotIn("inspect_power_profiles()", refresh)
        self.assertIn("self._start_power_profile_task(None)", refresh)
        apply = controller[controller.index("def applyPowerProfile"):controller.index("@Property(str, notify=launchStatusChanged)")]
        self.assertNotIn("set_power_profile(", apply)
        self.assertIn("self._start_power_profile_task(profile)", apply)
        self.assertIn("Une opération de gestion d'énergie est déjà en cours.", apply)

    def test_profile_backend_uses_only_native_powerprofilesctl(self):
        module = (ROOT / "gaming/backend/power_profiles.py").read_text(encoding="utf-8")
        self.assertIn('[executable, "get"]', module)
        self.assertIn('[executable, "list"]', module)
        self.assertIn('[executable, "set", profile]', module)
        self.assertNotIn("fancontrol", module)
        self.assertNotIn("sysfs", module)


if __name__ == "__main__":
    unittest.main()
