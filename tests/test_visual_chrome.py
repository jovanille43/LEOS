"""Tests for reversible LEOS Plasma splash and cursor activation."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from desktop.visual_chrome import PlasmaVisualChromeManager


class FakeKdeConfig:
    def __init__(self):
        self.values = {}

    def __call__(self, command, **_kwargs):
        executable = Path(command[0]).name
        args = command[1:]
        filename = Path(args[args.index("--file") + 1]).name
        groups = [args[index + 1] for index, value in enumerate(args[:-1]) if value == "--group"]
        group = groups[0] if len(groups) == 1 else tuple(groups)
        key = args[args.index("--key") + 1]
        identity = (filename, group, key)
        if executable == "kreadconfig6":
            return SimpleNamespace(returncode=0, stdout=self.values.get(identity, ""), stderr="")
        if executable == "kwriteconfig6":
            if "--delete" in args:
                self.values.pop(identity, None)
            else:
                self.values[identity] = args[-1]
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="unknown tool")


class PlasmaVisualChromeManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.config = root / "config"
        self.data = root / "data"
        self.state = root / "state"
        self.icons = root / "system-icons"
        self.look_and_feel = root / "look-and-feel"
        self.aurorae = self.data / "aurorae" / "themes"
        for directory in (self.config, self.data, self.icons, self.look_and_feel):
            directory.mkdir()
        self.aurorae.mkdir(parents=True)

        self.splash = self.look_and_feel / "org.leos.desktop"
        (self.splash / "contents" / "splash").mkdir(parents=True)
        (self.splash / "contents" / "splash" / "Splash.qml").write_text("Rectangle {}", encoding="utf-8")
        (self.splash / "manifest.json").write_text(json.dumps({
            "KPackageStructure": "Plasma/LookAndFeel",
            "KPlugin": {"Id": "org.leos.desktop"},
        }), encoding="utf-8")
        for theme_id in ("leos-custom-test", "leos-custom-a", "leos-custom-b"):
            cursor = self.data / "icons" / theme_id
            cursor.mkdir(parents=True)
            (cursor / "index.theme").write_text(f"[Icon Theme]\nName={theme_id}\n", encoding="utf-8")
            aurorae = self.aurorae / theme_id
            aurorae.mkdir(parents=True)
            (aurorae / "metadata.desktop").write_text(
                f"[Desktop Entry]\nName=LEOS\nX-KDE-PluginInfo-Name={theme_id}\n",
                encoding="utf-8",
            )
            (aurorae / f"{theme_id}rc").write_text("[General]\nTitleAlignment=Center\n", encoding="utf-8")

        self.wallpaper = root / "desktop-leos-ab.svg"
        self.wallpaper.write_text("<svg/>", encoding="utf-8")
        self.runner = FakeKdeConfig()
        self.manager = PlasmaVisualChromeManager(
            config_home=self.config,
            data_home=self.data,
            state_home=self.state,
            icon_theme_root=self.icons,
            look_and_feel_root=self.look_and_feel,
            command_lookup=lambda name: None if name in {"qdbus6", "qdbus"} else f"/usr/bin/{name}",
            runner=self.runner,
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_apply_and_restore_user_splash_and_cursor(self):
        self.runner.values[("ksplashrc", "KSplash", "Theme")] = "breeze"
        self.runner.values[("kcminputrc", "Mouse", "cursorTheme")] = "breeze_cursors"
        self.runner.values[("kwinrc", "org.kde.kdecoration2", "library")] = "org.kde.kwin3"
        self.runner.values[("kwinrc", "org.kde.kdecoration2", "theme")] = "Breeze"
        lockscreen_group = ("Greeter", "Wallpaper", "org.kde.image", "General")
        self.runner.values[("kscreenlockerrc", lockscreen_group, "Image")] = "/usr/share/backgrounds/default.jpg"
        self.runner.values[("kscreenlockerrc", lockscreen_group, "PreviewImage")] = "/usr/share/backgrounds/preview.jpg"
        message = self.manager.apply("org.leos.desktop", "leos-custom-test", "leos-custom-test", self.wallpaper.as_uri())
        self.assertIn("prochaine ouverture", message)
        self.assertEqual(self.runner.values[("ksplashrc", "KSplash", "Theme")], "org.leos.desktop")
        self.assertEqual(self.runner.values[("kcminputrc", "Mouse", "cursorTheme")], "leos-custom-test")
        self.assertEqual(self.runner.values[("kwinrc", "org.kde.kdecoration2", "library")], "org.kde.kwin.aurorae")
        self.assertEqual(self.runner.values[("kwinrc", "org.kde.kdecoration2", "theme")], "__aurorae__svg__leos-custom-test")
        self.assertEqual(self.runner.values[("kscreenlockerrc", lockscreen_group, "Image")], str(self.wallpaper))
        self.assertEqual(self.runner.values[("kscreenlockerrc", lockscreen_group, "PreviewImage")], str(self.wallpaper))
        self.assertTrue(self.manager.can_restore())
        self.manager.restore_previous()
        self.assertEqual(self.runner.values[("ksplashrc", "KSplash", "Theme")], "breeze")
        self.assertEqual(self.runner.values[("kcminputrc", "Mouse", "cursorTheme")], "breeze_cursors")
        self.assertEqual(self.runner.values[("kwinrc", "org.kde.kdecoration2", "library")], "org.kde.kwin3")
        self.assertEqual(self.runner.values[("kwinrc", "org.kde.kdecoration2", "theme")], "Breeze")
        self.assertEqual(self.runner.values[("kscreenlockerrc", lockscreen_group, "Image")], "/usr/share/backgrounds/default.jpg")
        self.assertEqual(self.runner.values[("kscreenlockerrc", lockscreen_group, "PreviewImage")], "/usr/share/backgrounds/preview.jpg")
        self.assertFalse(self.manager.can_restore())

    def test_reapplying_custom_cursor_preserves_original_rollback_target(self):
        self.runner.values[("ksplashrc", "KSplash", "Theme")] = "breeze"
        self.runner.values[("kcminputrc", "Mouse", "cursorTheme")] = "breeze_cursors"
        self.runner.values[("kwinrc", "org.kde.kdecoration2", "library")] = "org.kde.kwin3"
        self.runner.values[("kwinrc", "org.kde.kdecoration2", "theme")] = "Breeze"
        self.manager.apply("org.leos.desktop", "leos-custom-a", "leos-custom-a", self.wallpaper.as_uri())
        self.manager.apply("org.leos.desktop", "leos-custom-b", "leos-custom-b", self.wallpaper.as_uri())
        self.manager.restore_previous()
        self.assertEqual(self.runner.values[("ksplashrc", "KSplash", "Theme")], "breeze")
        self.assertEqual(self.runner.values[("kcminputrc", "Mouse", "cursorTheme")], "breeze_cursors")
        self.assertEqual(self.runner.values[("kwinrc", "org.kde.kdecoration2", "library")], "org.kde.kwin3")
        self.assertEqual(self.runner.values[("kwinrc", "org.kde.kdecoration2", "theme")], "Breeze")

    def test_restore_refuses_to_overwrite_a_user_change_after_leos(self):
        self.runner.values[("ksplashrc", "KSplash", "Theme")] = "breeze"
        self.runner.values[("kcminputrc", "Mouse", "cursorTheme")] = "breeze_cursors"
        self.manager.apply("org.leos.desktop", "leos-custom-test", "leos-custom-test", self.wallpaper.as_uri())
        self.runner.values[("kcminputrc", "Mouse", "cursorTheme")] = "adwaita"
        with self.assertRaisesRegex(RuntimeError, "préserver les choix récents"):
            self.manager.restore_previous()
        self.assertEqual(self.runner.values[("kcminputrc", "Mouse", "cursorTheme")], "adwaita")
        self.assertTrue(self.manager.can_restore())

    def test_restore_refuses_to_overwrite_a_manually_changed_window_decoration(self):
        self.runner.values[("ksplashrc", "KSplash", "Theme")] = "breeze"
        self.runner.values[("kcminputrc", "Mouse", "cursorTheme")] = "breeze_cursors"
        self.runner.values[("kwinrc", "org.kde.kdecoration2", "library")] = "org.kde.kwin3"
        self.runner.values[("kwinrc", "org.kde.kdecoration2", "theme")] = "Breeze"
        self.manager.apply("org.leos.desktop", "leos-custom-test", "leos-custom-test", self.wallpaper.as_uri())
        self.runner.values[("kwinrc", "org.kde.kdecoration2", "theme")] = "ManualChoice"
        with self.assertRaisesRegex(RuntimeError, "préserver les choix récents"):
            self.manager.restore_previous()
        self.assertEqual(self.runner.values[("kwinrc", "org.kde.kdecoration2", "theme")], "ManualChoice")

    def test_restore_refuses_to_overwrite_a_manually_changed_lock_screen_wallpaper(self):
        self.runner.values[("kscreenlockerrc", ("Greeter", "Wallpaper", "org.kde.image", "General"), "Image")] = "/usr/share/backgrounds/default.jpg"
        self.runner.values[("kscreenlockerrc", ("Greeter", "Wallpaper", "org.kde.image", "General"), "PreviewImage")] = "/usr/share/backgrounds/default.jpg"
        self.manager.apply(
            "org.leos.desktop", "leos-custom-test", "leos-custom-test", self.wallpaper.as_uri()
        )
        self.runner.values[("kscreenlockerrc", ("Greeter", "Wallpaper", "org.kde.image", "General"), "Image")] = "/home/user/custom-lockscreen.jpg"
        with self.assertRaisesRegex(RuntimeError, "préserver les choix récents"):
            self.manager.restore_previous()
        self.assertEqual(
            self.runner.values[("kscreenlockerrc", ("Greeter", "Wallpaper", "org.kde.image", "General"), "Image")],
            "/home/user/custom-lockscreen.jpg",
        )

    def test_missing_or_remote_lock_screen_wallpaper_is_rejected_before_changes(self):
        with self.assertRaises(ValueError):
            self.manager.apply("org.leos.desktop", "leos-custom-test", "leos-custom-test", "https://example.invalid/wallpaper.svg")
        with self.assertRaises(FileNotFoundError):
            self.manager.apply("org.leos.desktop", "leos-custom-test", "leos-custom-test", (Path(self.temp.name) / "missing.svg").as_uri())

    def test_missing_splash_package_or_cursor_is_rejected(self):
        with self.assertRaises(FileNotFoundError):
            self.manager.apply("missing.splash", "leos-custom-test", "leos-custom-test", self.wallpaper.as_uri())
        with self.assertRaises(FileNotFoundError):
            self.manager.apply("org.leos.desktop", "missing-cursor", "leos-custom-test", self.wallpaper.as_uri())
        with self.assertRaises(FileNotFoundError):
            self.manager.apply("org.leos.desktop", "leos-custom-test", "missing-aurorae", self.wallpaper.as_uri())

    def test_symlinked_user_config_is_never_modified(self):
        config_file = self.config / "ksplashrc"
        target = Path(self.temp.name) / "target"
        target.write_text("[KSplash]\nTheme=breeze\n", encoding="utf-8")
        config_file.symlink_to(target)
        with self.assertRaises(ValueError):
            self.manager.apply("org.leos.desktop", "leos-custom-test", "leos-custom-test", self.wallpaper.as_uri())
        self.assertEqual(target.read_text(encoding="utf-8"), "[KSplash]\nTheme=breeze\n")


if __name__ == "__main__":
    unittest.main()
