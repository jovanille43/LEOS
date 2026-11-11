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

    def test_mode_choice_does_not_add_automatic_application_closing(self):
        qml = (ROOT / "launcher" / "qml" / "ModeSelector.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn("resteront en arrière-plan", qml)
        self.assertNotIn("killall", qml)
        self.assertNotIn("pkill", qml)


if __name__ == "__main__":
    unittest.main()
