"""Tests for customized, reversible Plasma Style variants."""

import configparser
import json
import tempfile
import unittest
from pathlib import Path

from desktop.plasma_style import PlasmaStyleManager


class PlasmaStyleVariantTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.system = self.root / "system"
        theme = self.system / "leos"
        (theme / "widgets").mkdir(parents=True)
        (theme / "metadata.json").write_text(
            json.dumps({"KPlugin": {"Id": "leos", "Name": "LEOS"}}),
            encoding="utf-8",
        )
        self.source_svg = theme / "widgets" / "panel-background.svg"
        self.source_svg.write_text(
            '<svg><stop stop-color="#00D9FF"/><stop stop-color="#E33BFF"/>'
            '<path fill="#808080"/></svg>',
            encoding="utf-8",
        )
        self.data = self.root / "data"
        self.config = self.root / "config"
        self.state = self.root / "state"
        self.config.mkdir()
        self.config_file = self.config / "plasmarc"
        self.config_file.write_text("[Theme]\nname=Breeze\n", encoding="utf-8")
        self.commands = []

        def runner(command, **kwargs):
            self.commands.append(command)
            parser = configparser.ConfigParser(interpolation=None)
            parser.optionxform = str
            parser.read(self.config_file, encoding="utf-8")
            if not parser.has_section("Theme"):
                parser.add_section("Theme")
            parser.set("Theme", "name", command[1])
            with self.config_file.open("w", encoding="utf-8") as stream:
                parser.write(stream)
            return type("Result", (), {"returncode": 0, "stderr": ""})()

        self.manager = PlasmaStyleManager(
            data_home=self.data,
            config_home=self.config,
            state_home=self.state,
            system_theme_root=self.system,
            apply_executable="/usr/bin/plasma-apply-desktoptheme",
            runner=runner,
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_custom_style_is_user_scoped_and_restorable(self):
        message = self.manager.apply_custom_style("#FF8800", "#0055CC")
        selected = self.manager.current_style()
        self.assertIn("personnalisé", message.lower())
        self.assertTrue(selected.startswith("leos-ab-"))
        variant = self.data / "plasma" / "desktoptheme" / selected
        metadata = json.loads((variant / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["KPlugin"]["Id"], selected)
        svg = (variant / "widgets" / "panel-background.svg").read_text(encoding="utf-8")
        self.assertIn("#FF8800", svg)
        self.assertIn("#0055CC", svg)
        self.assertIn("#808080", svg)
        self.assertIn("#00D9FF", self.source_svg.read_text(encoding="utf-8"))
        self.assertTrue(self.manager.can_restore())
        self.manager.restore_previous_style()
        self.assertEqual(self.manager.current_style(), "Breeze")
        self.assertEqual(self.commands[1][1], "Breeze")


if __name__ == "__main__":
    unittest.main()
