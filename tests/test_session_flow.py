"""Tests for the LEOS startup and mode-selection contract."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SessionFlowTests(unittest.TestCase):
    def test_kde_autostart_opens_the_mode_selector(self):
        entry = (ROOT / "desktop" / "autostart" / "leos-session.desktop").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "Exec=/usr/bin/python3 /usr/share/leos/launcher/main.py --select",
            entry,
        )

    def test_selector_shows_clock_date_and_remembered_mode(self):
        qml = (ROOT / "launcher" / "qml" / "ModeSelector.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn("property date currentDate: new Date()", qml)
        self.assertIn('toLocaleTimeString(Qt.locale("fr_FR"), "HH:mm")', qml)
        self.assertIn('toLocaleDateString(Qt.locale("fr_FR"), "dddd d MMMM yyyy")', qml)
        self.assertIn("modeManager.lastMode", qml)
        self.assertIn("LEOS DESKTOP", qml)
        self.assertIn("LEOS GAMING", qml)

    def test_official_mode_emblems_have_separate_paths(self):
        qml = (ROOT / "launcher" / "qml" / "ModeSelector.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn("../../branding/desktop-logo.png", qml)
        self.assertIn("../../branding/gaming-logo.png", qml)

    def test_selector_accepts_read_only_controller_navigation(self):
        root = ROOT
        controller = (root / "launcher" / "controller.py").read_text(encoding="utf-8")
        main = (root / "launcher" / "main.py").read_text(encoding="utf-8")
        qml = (root / "launcher" / "qml" / "ModeSelector.qml").read_text(encoding="utf-8")
        self.assertIn("GamepadBackend()", controller)
        self.assertIn("mapper_from_preferences", controller)
        self.assertIn('setContextProperty("modeSelectorController", selector_controller)', main)
        self.assertIn("function onGamepadAction(action)", qml)
        self.assertIn("window.handleGamepadAction(action)", qml)

    def test_mode_choice_does_not_add_automatic_application_closing(self):
        qml = (ROOT / "launcher" / "qml" / "ModeSelector.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn("resteront en arrière-plan", qml)
        self.assertNotIn("killall", qml)
        self.assertNotIn("pkill", qml)

    def test_entering_and_leaving_gaming_requires_confirmation(self):
        selector = (ROOT / "launcher" / "qml" / "ModeSelector.qml").read_text(
            encoding="utf-8"
        )
        gaming = (ROOT / "gaming" / "qml" / "Main.qml").read_text(encoding="utf-8")
        self.assertIn('onClicked: transitionDialog.open()', selector)
        self.assertIn('modeManager.requestMode("gaming")', selector)
        self.assertIn('id: returnDialog', gaming)
        self.assertIn('title: "Retourner à Desktop Mode ?"', gaming)
        self.assertIn('returnDialog.open()', gaming)
        self.assertIn('leos.returnToDesktop()', gaming)
        self.assertIn('text: "CONFIRMER LE RETOUR AU DESKTOP"', gaming)


if __name__ == "__main__":
    unittest.main()
