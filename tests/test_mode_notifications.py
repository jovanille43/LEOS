"""Tests for mode transition notification wiring."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ModeNotificationTests(unittest.TestCase):
    def test_mode_selector_notifies_only_after_successful_mode_selection(self):
        source = (ROOT / "launcher/main.py").read_text(encoding="utf-8")
        self.assertIn("from desktop.notifications import post_notification", source)
        self.assertLess(source.index("manager.rememberMode(mode)"), source.index('post_notification("LEOS Gaming Mode"'))
        self.assertIn('post_notification("LEOS Desktop Mode"', source)
        self.assertIn('post_notification("LEOS Gaming Mode"', source)
        self.assertIn('"success", native=False)', source)

    def test_gaming_return_to_desktop_is_recorded(self):
        source = (ROOT / "gaming/backend/controller.py").read_text(encoding="utf-8")
        self.assertIn("from desktop.notifications import post_notification", source)
        self.assertIn('post_notification("Retour à Desktop Mode"', source)
        self.assertIn("native=False", source)
        self.assertLess(source.index('self.settings.set("last_mode", "desktop")'), source.index('post_notification("Retour à Desktop Mode"'))

    def test_mode_notification_does_not_use_native_popup_command(self):
        source = (ROOT / "launcher/main.py").read_text(encoding="utf-8")
        self.assertNotIn("notify-send", source)
        self.assertNotIn("subprocess.run", source)


if __name__ == "__main__":
    unittest.main()
