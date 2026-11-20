"""Tests for reversible activation of the LEOS Plasma icon theme."""

import configparser
import tempfile
import unittest
from pathlib import Path

from desktop.icon_theme import ICON_THEME, PlasmaIconThemeManager


class PlasmaIconThemeManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = self.root / "config"
        self.data = self.root / "data"
        self.state = self.root / "state"
        self.icons = self.root / "icons"
        (self.icons / ICON_THEME).mkdir(parents=True)
        (self.icons / ICON_THEME / "scalable" / "actions").mkdir(parents=True)
        (self.icons / ICON_THEME / "scalable" / "actions" / "leos-test.svg").write_text(
            '<svg><path stroke="#00D9FF"/><path fill="#E33BFF"/><path fill="#808080"/></svg>',
            encoding="utf-8",
        )
        (self.icons / ICON_THEME / "index.theme").write_text(
            "[Icon Theme]\nName=LEOS\nInherits=breeze,hicolor\n",
            encoding="utf-8",
        )
        self.config.mkdir()
        self.config_file = self.config / "kdeglobals"
        self.config_file.write_text("[Icons]\nTheme=breeze\n", encoding="utf-8")
        self.commands = []

        def runner(command, **kwargs):
            self.commands.append((command, kwargs))
            parser = configparser.ConfigParser(interpolation=None)
            parser.optionxform = str
            parser.read(self.config_file, encoding="utf-8")
            if not parser.has_section("Icons"):
                parser.add_section("Icons")
            parser.set("Icons", "Theme", command[1])
            with self.config_file.open("w", encoding="utf-8") as stream:
                parser.write(stream)
            return type("Result", (), {"returncode": 0, "stderr": ""})()

        self.manager = PlasmaIconThemeManager(
            config_home=self.config,
            data_home=self.data,
            state_home=self.state,
            system_icon_root=self.icons,
            apply_executable="/usr/libexec/plasma-changeicons",
            runner=runner,
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_applies_leos_icon_theme_and_restores_previous_theme(self):
        self.assertTrue(self.manager.theme_installed())
        self.assertTrue(self.manager.tool_available())
        self.assertEqual(self.manager.current_theme(), "breeze")
        self.assertIn("LEOS", self.manager.apply_theme())
        self.assertEqual(self.manager.current_theme(), "leos")
        self.assertTrue(self.manager.can_restore())
        self.assertEqual(self.manager.restore_previous_theme(), "Thème d'icônes précédent restauré : breeze.")
        self.assertEqual(self.manager.current_theme(), "breeze")
        self.assertFalse(self.manager.can_restore())
        self.assertEqual([command[0][1] for command in self.commands], ["leos", "breeze"])

    def test_custom_a_b_icon_variant_is_user_scoped_and_restorable(self):
        message = self.manager.apply_custom_theme("#FF8800", "#0055CC")
        selected = self.manager.current_theme()
        self.assertIn("personnalisé", message.lower())
        self.assertTrue(selected.startswith("leos-ab-"))
        variant = self.data / "icons" / selected
        index = (variant / "index.theme").read_text(encoding="utf-8")
        self.assertIn("Name=LEOS personnalisé", index)
        svg = (variant / "scalable" / "actions" / "leos-test.svg").read_text(encoding="utf-8")
        self.assertIn("#FF8800", svg)
        self.assertIn("#0055CC", svg)
        self.assertIn("#808080", svg)
        self.assertIn("#00D9FF", (self.icons / ICON_THEME / "scalable" / "actions" / "leos-test.svg").read_text(encoding="utf-8"))
        self.assertTrue(self.manager.can_restore())
        self.manager.restore_previous_theme()
        self.assertEqual(self.manager.current_theme(), "breeze")

    def test_applies_custom_user_scoped_theme_id_and_restores_original(self):
        custom = self.data / "icons" / "leos-custom-abcdef0123456789"
        custom.mkdir(parents=True)
        (custom / "index.theme").write_text(
            "[Icon Theme]\nName=LEOS personnalisé\nInherits=breeze,hicolor\n",
            encoding="utf-8",
        )
        self.assertTrue(self.manager.theme_installed(custom.name))
        self.assertIn("personnalisé", self.manager.apply_theme(custom.name).lower())
        self.assertEqual(self.manager.current_theme(), custom.name)
        self.assertEqual(self.manager._read_state()["previous_theme"], "breeze")
        self.manager.restore_previous_theme()
        self.assertEqual(self.manager.current_theme(), "breeze")

    def test_cannot_apply_when_active_theme_cannot_be_identified(self):
        self.config_file.write_text("[General]\nColorScheme=BreezeDark\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "ne peut pas être identifié"):
            self.manager.apply_theme()
        self.assertEqual(self.commands, [])

    def test_cannot_apply_when_leos_icon_package_is_missing(self):
        (self.icons / ICON_THEME / "index.theme").unlink()
        with self.assertRaisesRegex(FileNotFoundError, "paquet du thème d'icônes LEOS"):
            self.manager.apply_theme()
        self.assertEqual(self.commands, [])

    def test_icon_theme_identifier_is_not_taken_from_user_input(self):
        with self.assertRaisesRegex(ValueError, "Identifiant de thème d'icônes KDE invalide"):
            self.manager._apply("../outside")
        self.assertEqual(self.commands, [])

    def test_corrupt_restore_state_is_not_used(self):
        state_dir = self.state / "leos"
        state_dir.mkdir(parents=True)
        (state_dir / "icon-theme.json").write_text(
            '{"schema_version": 1, "managed_by": "LEOS Plasma Icon Theme Manager", "previous_theme": "../outside"}',
            encoding="utf-8",
        )
        self.assertFalse(self.manager.can_restore())
        with self.assertRaises(FileNotFoundError):
            self.manager.restore_previous_theme()
        self.assertEqual(self.commands, [])


if __name__ == "__main__":
    unittest.main()
