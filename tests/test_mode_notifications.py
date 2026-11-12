"""Tests for mode transition notification wiring."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ModeNotificationTests(unittest.TestCase):
    def test_desktop_is_remembered_by_selector_and_gaming_after_qml_load(self):
        launcher = (ROOT / "launcher/main.py").read_text(encoding="utf-8")
        gaming = (ROOT / "gaming/main.py").read_text(encoding="utf-8")
        controller = (ROOT / "gaming/backend/controller.py").read_text(encoding="utf-8")

        self.assertIn('manager.rememberMode("desktop")', launcher)
        self.assertNotIn('manager.rememberMode("gaming")', launcher)
        self.assertIn('"LEOS Desktop Mode",', launcher)
        self.assertNotIn('post_notification("LEOS Gaming Mode"', launcher)
        self.assertIn('"LEOS Gaming Mode",', gaming)
        self.assertIn('"L\'interface Gaming a démarré."', gaming)
        self.assertLess(
            gaming.index("if not engine.rootObjects():"),
            gaming.index('controller.settings.set("last_mode", "gaming")'),
        )
        self.assertNotIn('self.settings.set("last_mode", "gaming")', controller)


    def test_gaming_return_to_desktop_is_recorded(self):
        source = (ROOT / "gaming/backend/controller.py").read_text(encoding="utf-8")
        self.assertIn("from desktop.notifications import post_notification", source)
        self.assertIn('post_notification("Retour à Desktop Mode"', source)
        self.assertIn("native=False", source)
        self.assertLess(source.index('self.settings.set("last_mode", "desktop")'), source.index('post_notification("Retour à Desktop Mode"'))

    def test_settings_write_failure_does_not_abort_mode_launch(self):
        manager = (ROOT / "launcher/mode_manager.py").read_text(encoding="utf-8")
        launcher = (ROOT / "launcher/main.py").read_text(encoding="utf-8")
        gaming = (ROOT / "gaming/main.py").read_text(encoding="utf-8")
        self.assertIn("except (OSError, ValueError, TypeError, KeyError)", manager)
        self.assertIn("return False", manager[manager.index("def rememberMode"):])
        self.assertIn("remembered = manager.rememberMode(\"desktop\")", launcher)
        self.assertIn("if remembered else \"warning\"", launcher)
        self.assertIn("try:\n        controller.settings.set(\"last_mode\", \"gaming\")", gaming)
        self.assertIn("startup_priority = \"warning\"", gaming)
        self.assertIn("controller.monitor.start()", gaming)

    def test_mode_manager_rejects_non_string_and_unknown_mode_values(self):
        manager = (ROOT / "launcher/mode_manager.py").read_text(encoding="utf-8")
        self.assertIn('if not isinstance(mode, str) or mode not in {"desktop", "gaming"}:', manager)
        self.assertIn("def rememberMode(self, mode: str) -> bool:", manager)

    def test_mode_notification_does_not_use_native_popup_command(self):
        source = (ROOT / "launcher/main.py").read_text(encoding="utf-8")
        self.assertNotIn("notify-send", source)
        self.assertNotIn("subprocess.run", source)


if __name__ == "__main__":
    unittest.main()
