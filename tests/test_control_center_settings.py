"""Tests for safe shortcuts to native KDE settings modules."""

import re
import unittest
from pathlib import Path

from control_center.settings_modules import (
    SETTINGS_MODULES,
    general_settings_command,
    settings_module_command,
    system_monitor_command,
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

    def test_wallpaper_module_opens_the_native_kde_picker(self):
        self.assertEqual(
            settings_module_command(
                "wallpaper",
                lambda name: "/usr/bin/kcmshell6" if name == "kcmshell6" else None,
            ),
            ["/usr/bin/kcmshell6", "kcm_wallpaper"],
        )
        self.assertEqual(SETTINGS_MODULES["wallpaper"], "kcm_wallpaper")

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

    def test_native_system_monitor_is_opened_only_when_installed(self):
        self.assertEqual(
            system_monitor_command(
                lambda name: "/usr/bin/plasma-systemmonitor" if name == "plasma-systemmonitor" else None
            ),
            ["/usr/bin/plasma-systemmonitor"],
        )
        self.assertIsNone(system_monitor_command(lambda _name: None))

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
        self.assertTrue(sections.issubset(set(SETTINGS_MODULES)))
        self.assertIn("wallpaper", SETTINGS_MODULES)

    def test_appearance_exposes_both_leos_wallpapers_and_native_kde_selection(self):
        root = Path(__file__).resolve().parents[1]
        qml = (root / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("source: themeManager.assets.desktop_wallpaper", qml)
        self.assertIn("source: themeManager.assets.gaming_wallpaper", qml)
        self.assertEqual(qml.count("fillMode: Image.PreserveAspectFit"), 2)
        wallpaper_start = qml.index("FONDS D")
        wallpaper_end = qml.index("THÈME KDE PLASMA", wallpaper_start)
        self.assertNotIn("Image.PreserveAspectCrop", qml[wallpaper_start:wallpaper_end])
        self.assertIn('controlCenter.openSettingsModule("wallpaper")', qml)
        modules = (root / "control_center/settings_modules.py").read_text(encoding="utf-8")
        self.assertIn('"wallpaper": "kcm_wallpaper"', modules)
        self.assertIn("rien n'est appliqué sans ton choix dans KDE", qml)

    def test_animation_and_sound_preferences_are_exposed_as_shared_controls(self):
        root = Path(__file__).resolve().parents[1]
        qml = (root / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        controller = (root / "control_center/controller.py").read_text(encoding="utf-8")
        settings = (root / "leos_core/settings.py").read_text(encoding="utf-8")

        self.assertIn('Label { text: "Animations LEOS"', qml)
        self.assertIn("checked: controlCenter.animationsEnabled", qml)
        self.assertIn("controlCenter.setAnimationsEnabled(checked)", qml)
        self.assertIn('Label { text: "Sons LEOS"', qml)
        self.assertIn("checked: controlCenter.soundsEnabled", qml)
        self.assertIn("controlCenter.setSoundsEnabled(checked)", qml)
        self.assertIn('def animationsEnabled(self)', controller)
        self.assertIn('def soundsEnabled(self)', controller)
        self.assertIn('self.settings.set("animations_enabled", enabled)', controller)
        self.assertIn('self.settings.set("sounds_enabled", enabled)', controller)
        self.assertIn('"animations_enabled": True', settings)
        self.assertIn('"sounds_enabled": True', settings)

    def test_settings_navigation_button_content_uses_explicit_id(self):
        qml = (Path(__file__).resolve().parents[1] / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("id: settingsNavigationButton", qml)
        self.assertIn("text: settingsNavigationButton.text", qml)
        self.assertNotIn("text: parent.text", qml)

    def test_overview_uses_real_shared_monitor_values(self):
        root = Path(__file__).resolve().parents[1]
        qml = (root / "control_center" / "qml" / "Main.qml").read_text(encoding="utf-8")
        controller = (root / "control_center" / "controller.py").read_text(encoding="utf-8")
        main = (root / "control_center" / "main.py").read_text(encoding="utf-8")
        monitor = (root / "gaming" / "backend" / "system_monitor.py").read_text(encoding="utf-8")
        self.assertIn("systemMonitor.cpuUsage", qml)
        self.assertIn("systemMonitor.memoryUsage", qml)
        self.assertIn("systemMonitor.cpuTemperature >= 0", qml)
        self.assertIn("systemMonitor.diskUsage >= 0", qml)
        self.assertIn("systemMonitor.networkReceiveRate", qml)
        self.assertIn("systemMonitor.networkSendRate", qml)
        self.assertIn("from gaming.backend.system_monitor import SystemMonitor", controller)
        self.assertIn('context.setContextProperty("systemMonitor", controller.monitor)', main)
        self.assertIn("self._timer.setInterval(2000)", monitor)
        self.assertIn("psutil.disk_usage(\"/\")", monitor)
        self.assertIn("psutil.net_io_counters()", monitor)
        self.assertIn("time.monotonic()", monitor)


    def test_appearance_exposes_confirmed_user_scoped_kde_resource_export(self):
        root = Path(__file__).resolve().parents[1]
        qml = (root / "control_center" / "qml" / "Main.qml").read_text(encoding="utf-8")
        controller = (root / "control_center" / "controller.py").read_text(encoding="utf-8")
        assets = (root / "desktop" / "theme_assets.py").read_text(encoding="utf-8")

        self.assertIn("id: kdeResourcesConfirmation", qml)
        self.assertIn("onAccepted: window.kdeResourceNotice = controlCenter.exportKdeThemeResources()", qml)
        self.assertIn("Installer les ressources dans mon profil", qml)
        self.assertIn("controlCenter.kdeThemeResourcesAvailable", qml)
        self.assertIn("def exportKdeThemeResources(self)", controller)
        self.assertIn("self.themeAssets.export_kde_resource_packages_for_theme(self.theme)", controller)
        self.assertIn("def export_kde_resource_packages_for_theme(", assets)
        self.assertIn("sans activation", assets)
        self.assertIn("plasma", assets)
        self.assertIn("aurorae", assets)


if __name__ == "__main__":
    unittest.main()
