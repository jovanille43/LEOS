"""Tests for reversible application of LEOS KDE visual themes."""
from __future__ import annotations

import configparser
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from desktop.kde_visual_theme import KdeVisualThemeManager
from desktop.plasma_style import PlasmaStyleManager
from desktop.theme_assets import ThemeAssetManager


class FakeKdeRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], dict]] = []
        self.fail_next: set[str] = set()

    def __call__(self, args, **kwargs):
        arguments = list(args)
        self.calls.append((arguments, kwargs))
        executable = Path(arguments[0]).name
        if executable in self.fail_next:
            self.fail_next.remove(executable)
            return SimpleNamespace(returncode=1, stderr="simulated failure")

        if executable == "kwriteconfig6":
            self._write_kconfig(arguments)
        elif executable == "plasma-apply-desktoptheme":
            self._write_value(
                Path(self.plasmarc),
                "Theme",
                "name",
                arguments[1],
            )
        return SimpleNamespace(returncode=0, stderr="")

    @staticmethod
    def _write_value(path: Path, group: str, key: str, value: str | None) -> None:
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        parser.optionxform = str
        if path.is_file():
            parser.read(path, encoding="utf-8")
        if not parser.has_section(group):
            parser.add_section(group)
        if value is None:
            parser.remove_option(group, key)
        else:
            parser.set(group, key, value)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as stream:
            parser.write(stream)

    def _write_kconfig(self, args: list[str]) -> None:
        path = Path(args[args.index("--file") + 1])
        group = args[args.index("--group") + 1]
        key = args[args.index("--key") + 1]
        value = None if "--delete" in args else args[-1]
        self._write_value(path, group, key, value)


class KdeVisualThemeManagerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.data_home = self.root / "data"
        self.config_home = self.root / "config"
        self.state_home = self.root / "state"
        self.config_home.mkdir()
        self.data_home.mkdir()

        self.kdeglobals = self.config_home / "kdeglobals"
        self.kdeglobals.write_text(
            "[Icons]\nTheme=breeze\n",
            encoding="utf-8",
        )
        self.plasmarc = self.config_home / "plasmarc"
        self.plasmarc.write_text(
            "[Theme]\nname=breeze-dark\n",
            encoding="utf-8",
        )
        self.kwinrc = self.config_home / "kwinrc"
        self.kwinrc.write_text(
            "[org.kde.kdecoration2]\nlibrary=org.kde.kwin.breeze\ntheme=Breeze\n",
            encoding="utf-8",
        )

        self.branding = self.root / "branding"
        self.branding.mkdir()
        self.icon_source = self.root / "source-icons" / "leos"
        (self.icon_source / "scalable" / "apps").mkdir(parents=True)
        (self.icon_source / "scalable" / "apps" / "leos-test.svg").write_text(
            '<svg><path fill="#00D9FF"/></svg>', encoding="utf-8"
        )
        (self.icon_source / "index.theme").write_text(
            "[Icon Theme]\nName=LEOS\nComment=LEOS icons\nInherits=breeze,hicolor\n",
            encoding="utf-8",
        )
        self.plasma_source = self.root / "source-plasma" / "leos"
        (self.plasma_source / "widgets").mkdir(parents=True)
        (self.plasma_source / "widgets" / "background.svg").write_text(
            '<svg><path fill="#E33BFF"/></svg>', encoding="utf-8"
        )
        (self.plasma_source / "metadata.json").write_text(
            json.dumps({"KPlugin": {"Id": "leos", "Name": "LEOS"}}),
            encoding="utf-8",
        )
        self.aurorae_source = self.root / "source-aurorae" / "leos"
        self.aurorae_source.mkdir(parents=True)
        for filename in ("decoration.svg", "close.svg"):
            (self.aurorae_source / filename).write_text(
                '<svg><path stroke="#00D9FF"/></svg>', encoding="utf-8"
            )
        (self.aurorae_source / "leosrc").write_text(
            "[General]\nTitleAlignment=Center\n", encoding="utf-8"
        )
        (self.aurorae_source / "metadata.desktop").write_text(
            "[Desktop Entry]\nName=LEOS\nComment=LEOS Aurorae\n"
            "X-KDE-PluginInfo-Name=leos\nType=Application\n",
            encoding="utf-8",
        )

        self.assets = ThemeAssetManager(
            branding_dir=self.branding,
            cache_dir=self.root / "cache",
            icon_theme_dir=self.icon_source,
            plasma_theme_dir=self.plasma_source,
            aurorae_theme_dir=self.aurorae_source,
        )
        for theme in ("light", "gaming"):
            self.assets.export_kde_resource_packages_for_theme(
                theme, data_directory=self.data_home
            )

        self.runner = FakeKdeRunner()
        self.runner.plasmarc = self.plasmarc
        executables = {
            "kwriteconfig6": "/usr/bin/kwriteconfig6",
            "plasma-apply-desktoptheme": "/usr/bin/plasma-apply-desktoptheme",
            "qdbus6": "/usr/bin/qdbus6",
            "gdbus": "/usr/bin/gdbus",
        }
        finder = lambda name: executables.get(name)
        self.plasma = PlasmaStyleManager(
            data_home=self.data_home,
            config_home=self.config_home,
            state_home=self.state_home,
            system_theme_root=self.root / "system-plasma",
            apply_executable=executables["plasma-apply-desktoptheme"],
            runner=self.runner,
        )
        self.manager = KdeVisualThemeManager(
            assets=self.assets,
            plasma_style=self.plasma,
            config_home=self.config_home,
            state_home=self.state_home,
            data_home=self.data_home,
            runner=self.runner,
            find_executable=finder,
        )

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def _config_value(path: Path, group: str, key: str) -> str | None:
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        parser.optionxform = str
        parser.read(path, encoding="utf-8")
        return parser.get(group, key, fallback=None)

    def test_apply_changes_icons_plasma_and_aurorae_together(self):
        message = self.manager.apply_theme("light")

        self.assertIn("icônes, à Plasma et aux décorations", message)
        self.assertEqual(self.manager._state()["theme"], "light")
        self.assertTrue(self.manager.can_restore())
        self.assertEqual(
            self.manager._state()["previous_icons"],
            "breeze",
        )
        self.assertEqual(
            self.manager._state()["previous_plasma"],
            "breeze-dark",
        )
        self.assertEqual(
            self.manager._state()["previous_aurorae_theme"],
            "Breeze",
        )

        self.assertEqual(self._config_value(self.kdeglobals, "Icons", "Theme"), "leos-light")
        self.assertEqual(self.plasma.current_style(), "leos-light")
        self.assertEqual(self._config_value(self.kwinrc, "org.kde.kdecoration2", "library"), "org.kde.kwin.aurorae")
        self.assertEqual(self._config_value(self.kwinrc, "org.kde.kdecoration2", "theme"), "__aurorae__svg__leos-light")
        self.assertTrue((self.data_home / "aurorae" / "themes" / "leos-light" / "leos-lightrc").is_file())
        self.assertTrue(any(Path(call[0][0]).name == "qdbus6" for call in self.runner.calls))
        self.assertTrue(any(Path(call[0][0]).name == "gdbus" for call in self.runner.calls))

    def test_restore_returns_all_components_to_their_previous_values(self):
        self.manager.apply_theme("light")
        message = self.manager.restore_previous_theme()

        self.assertIn("restauré", message)
        self.assertFalse(self.manager.can_restore())
        self.assertEqual(self._config_value(self.kdeglobals, "Icons", "Theme"), "breeze")
        self.assertEqual(self.plasma.current_style(), "breeze-dark")
        self.assertEqual(self._config_value(self.kwinrc, "org.kde.kdecoration2", "library"), "org.kde.kwin.breeze")
        self.assertEqual(self._config_value(self.kwinrc, "org.kde.kdecoration2", "theme"), "Breeze")
        self.assertFalse(self.plasma.can_restore())

    def test_switching_between_leos_palettes_keeps_the_original_rollback_target(self):
        self.manager.apply_theme("light")
        self.manager.apply_theme("gaming")

        self.assertEqual(self.manager._state()["previous_icons"], "breeze")
        self.assertEqual(self.manager._state()["previous_plasma"], "breeze-dark")
        self.assertEqual(self.manager._state()["previous_aurorae_theme"], "Breeze")
        self.assertEqual(self._config_value(self.kdeglobals, "Icons", "Theme"), "leos-gaming")
        self.assertEqual(self.plasma.current_style(), "leos-gaming")
        self.manager.restore_previous_theme()
        self.assertEqual(self._config_value(self.kdeglobals, "Icons", "Theme"), "breeze")
        self.assertEqual(self.plasma.current_style(), "breeze-dark")

    def test_restore_preserves_components_changed_manually_after_leos_application(self):
        self.manager.apply_theme("light")
        FakeKdeRunner._write_value(self.kdeglobals, "Icons", "Theme", "Papirus")
        message = self.manager.restore_previous_theme()

        self.assertIn("icônes modifiées", message)
        self.assertEqual(self._config_value(self.kdeglobals, "Icons", "Theme"), "Papirus")
        self.assertEqual(self.plasma.current_style(), "breeze-dark")
        self.assertEqual(self._config_value(self.kwinrc, "org.kde.kdecoration2", "theme"), "Breeze")

    def test_partial_kwin_failure_rolls_back_all_already_applied_components(self):
        self.runner.fail_next.add("qdbus6")

        with self.assertRaises(RuntimeError):
            self.manager.apply_theme("light")

        self.assertIn("Theme=breeze", self.kdeglobals.read_text(encoding="utf-8"))
        self.assertEqual(self.plasma.current_style(), "breeze-dark")
        self.assertEqual(self._config_value(self.kwinrc, "org.kde.kdecoration2", "library"), "org.kde.kwin.breeze")
        self.assertIn("theme=Breeze", self.kwinrc.read_text(encoding="utf-8"))
        self.assertFalse(self.manager.can_restore())
        self.assertFalse(self.plasma.can_restore())

    def test_application_requires_all_three_exported_resources(self):
        manager = KdeVisualThemeManager(
            assets=ThemeAssetManager(
                branding_dir=self.branding,
                cache_dir=self.root / "empty-cache",
                icon_theme_dir=self.icon_source,
                plasma_theme_dir=self.root / "missing-plasma",
                aurorae_theme_dir=self.aurorae_source,
            ),
            plasma_style=self.plasma,
            config_home=self.config_home,
            state_home=self.state_home,
            data_home=self.data_home,
            runner=self.runner,
            find_executable=lambda name: "/usr/bin/" + name,
        )
        with self.assertRaises(FileNotFoundError):
            manager.apply_theme("light")
        self.assertIn("Theme=breeze", self.kdeglobals.read_text(encoding="utf-8"))
        self.assertEqual(self.plasma.current_style(), "breeze-dark")

    def test_existing_invalid_state_is_never_overwritten(self):
        state_dir = self.state_home / "leos"
        state_dir.mkdir(parents=True)
        self.manager.state_file.write_text("{broken", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.manager.apply_theme("light")
        self.assertEqual(self.manager.state_file.read_text(encoding="utf-8"), "{broken")
        self.assertIn("Theme=breeze", self.kdeglobals.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
