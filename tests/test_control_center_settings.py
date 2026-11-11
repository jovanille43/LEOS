"""Tests for safe shortcuts to native KDE settings modules."""

import re
import unittest
from pathlib import Path

from control_center.settings_modules import (
    SETTINGS_MODULES,
    general_settings_command,
    settings_module_command,
)


class SettingsModuleCommandTests(unittest.TestCase):
    def test_known_sections_resolve_to_expected_modules(self):
        self.assertEqual(
            settings_module_command(
                "bluetooth",
                lambda name: "/usr/bin/kcmshell6" if name == "kcmshell6" else None,
            ),
            ["/usr/bin/kcmshell6", "kcm_bluetooth"],
        )
        self.assertEqual(
            settings_module_command(
                "network",
                lambda name: "/usr/bin/kcmshell6" if name == "kcmshell6" else None,
            ),
            ["/usr/bin/kcmshell6", "kcm_networkmanagement"],
        )

    def test_uses_system_settings_when_standalone_shell_is_missing(self):
        def finder(name):
            return "/usr/bin/systemsettings" if name == "systemsettings" else None

        self.assertEqual(
            settings_module_command("audio", finder),
            ["/usr/bin/systemsettings", "kcm_pulseaudio"],
        )

    def test_unknown_section_is_rejected_without_executables(self):
        self.assertIsNone(settings_module_command("arbitrary-command", lambda _name: None))
        self.assertNotIn("arbitrary-command", SETTINGS_MODULES)

    def test_missing_kde_tools_returns_no_command(self):
        self.assertIsNone(settings_module_command("bluetooth", lambda _name: None))
        self.assertIsNone(general_settings_command(lambda _name: None))

    def test_general_settings_command_has_no_user_arguments(self):
        self.assertEqual(
            general_settings_command(
                lambda name: "/usr/bin/systemsettings" if name == "systemsettings" else None
            ),
            ["/usr/bin/systemsettings"],
        )

    def test_qml_hardware_sections_match_the_allowlist(self):
        qml_path = Path(__file__).resolve().parents[1] / "control_center" / "qml" / "Main.qml"
        qml = qml_path.read_text(encoding="utf-8")
        sections = set(re.findall(r'section: "([a-z-]+)"', qml))
        self.assertEqual(sections, set(SETTINGS_MODULES))


if __name__ == "__main__":
    unittest.main()
