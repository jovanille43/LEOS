"""Visual contracts for LEOS login and session-start surfaces."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BootSurfaceVisualTests(unittest.TestCase):
    def test_sddm_login_has_a_graphite_card_and_explicit_credentials_hierarchy(self):
        qml = (ROOT / "branding/sddm/leos/Main.qml").read_text(encoding="utf-8")
        self.assertIn("id: loginCard", qml)
        self.assertIn("id: loginContent", qml)
        self.assertIn('text: "IDENTIFIANT"', qml)
        self.assertIn('text: "MOT DE PASSE"', qml)
        self.assertIn('userField.activeFocus ? "#00D9FF"', qml)
        self.assertIn('passwordField.activeFocus ? "#E33BFF"', qml)
        self.assertIn('GradientStop { position: 0; color: loginButton.down ? "#00B7D8" : "#00D9FF" }', qml)
        self.assertIn("sddm.login(userField.text.trim(), passwordField.text, selectedSession)", qml)

    def test_sddm_power_actions_stay_separate_and_confirmed(self):
        qml = (ROOT / "branding/sddm/leos/Main.qml").read_text(encoding="utf-8")
        self.assertIn("function requestPowerAction(action)", qml)
        self.assertIn("powerConfirmation.open()", qml)
        self.assertIn("sddm.powerOff()", qml)
        self.assertIn("sddm.reboot()", qml)
        self.assertIn("sddm.suspend()", qml)

    def test_plasma_splash_uses_a_quiet_a_b_identity_and_progress_indicator(self):
        qml = (ROOT / "plasma-theme/look-and-feel/org.leos.desktop/contents/splash/Splash.qml").read_text(encoding="utf-8")
        self.assertIn('text: "DESKTOP ENVIRONMENT"', qml)
        self.assertIn('GradientStop { position: 0; color: "#00D9FF" }', qml)
        self.assertIn('GradientStop { position: 1; color: "#E33BFF" }', qml)
        self.assertIn("SequentialAnimation on x", qml)
        self.assertIn('root.stage < 1 ? "Initialisation de votre environnement"', qml)


if __name__ == "__main__":
    unittest.main()
