"""Tests for robust XDG directory resolution."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from leos_core.paths import config_home, data_home, state_home
from leos_core.settings import SettingsStore
from desktop.dock_favourites import DockFavourites
from desktop.notification_store import NotificationStore
from desktop.recent_applications import RecentApplications
from desktop.layouts import DesktopLayoutStore
from desktop.plasma_backup import PlasmaBackupManager
from desktop.kde_colors import KdeColorSchemeManager
from desktop.plasma_style import PlasmaStyleManager
from controller_center.profiles import ControllerProfileStore, config_path as controller_config_path


class XdgPathTests(unittest.TestCase):
    def test_defaults_are_used_when_environment_variables_are_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            with patch.dict(os.environ, {"HOME": str(home)}, clear=True):
                self.assertEqual(config_home(), home / ".config")
                self.assertEqual(data_home(), home / ".local" / "share")
                self.assertEqual(state_home(), home / ".local" / "state")

    def test_empty_and_relative_xdg_values_fall_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            environment = {
                "HOME": str(home),
                "XDG_CONFIG_HOME": "",
                "XDG_DATA_HOME": "relative/data",
                "XDG_STATE_HOME": "relative/state",
            }
            with patch.dict(os.environ, environment, clear=True):
                self.assertEqual(config_home(), home / ".config")
                self.assertEqual(data_home(), home / ".local" / "share")
                self.assertEqual(state_home(), home / ".local" / "state")

    def test_absolute_xdg_values_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            environment = {
                "XDG_CONFIG_HOME": str(root / "cfg"),
                "XDG_DATA_HOME": str(root / "data"),
                "XDG_STATE_HOME": str(root / "state"),
            }
            with patch.dict(os.environ, environment, clear=True):
                self.assertEqual(config_home(), root / "cfg")
                self.assertEqual(data_home(), root / "data")
                self.assertEqual(state_home(), root / "state")

    def test_tilde_is_expanded_before_absolute_path_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            with patch.dict(os.environ, {"HOME": str(home), "XDG_CONFIG_HOME": "~/leos-config"}, clear=True):
                self.assertEqual(config_home(), home / "leos-config")

    def test_application_stores_use_the_configured_xdg_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "config"
            data = root / "data"
            state = root / "state"
            environment = {
                "HOME": str(root / "home"),
                "XDG_CONFIG_HOME": str(config),
                "XDG_DATA_HOME": str(data),
                "XDG_STATE_HOME": str(state),
            }
            with patch.dict(os.environ, environment, clear=True):
                self.assertEqual(SettingsStore().path, config / "leos" / "settings.json")
                self.assertEqual(DockFavourites().path, config / "leos" / "dock-favourites.json")
                self.assertEqual(DesktopLayoutStore().path, config / "leos" / "desktop-layout.json")
                self.assertEqual(ControllerProfileStore().path, config / "leos" / "controllers.json")
                self.assertEqual(controller_config_path(), config / "leos" / "controllers.json")
                self.assertEqual(NotificationStore().path, state / "leos" / "notifications.json")
                self.assertEqual(
                    RecentApplications().path,
                    state / "leos" / "recent-applications.json",
                )
                backup = PlasmaBackupManager()
                self.assertEqual(
                    backup.config_path,
                    config / "plasma-org.kde.plasma.desktop-appletsrc",
                )
                self.assertEqual(backup.backup_dir, state / "leos" / "plasma-backups")
                colors = KdeColorSchemeManager()
                self.assertEqual(colors.data_home, data)
                self.assertEqual(colors.config_file, config / "kdeglobals")
                self.assertEqual(colors.state_file, state / "leos" / "kde-color-scheme.json")
                style = PlasmaStyleManager()
                self.assertEqual(style.user_theme_root, data / "plasma" / "desktoptheme")
                self.assertEqual(style.config_file, config / "plasmarc")
                self.assertEqual(style.state_file, state / "leos" / "plasma-style.json")

    def test_gaming_library_routes_data_paths_through_shared_xdg_helper(self):
        source = (
            Path(__file__).resolve().parents[1] / "gaming" / "backend" / "library.py"
        ).read_text(encoding="utf-8")
        self.assertIn("from leos_core.paths import data_home as xdg_data_home", source)
        self.assertGreaterEqual(source.count("xdg_data_home()"), 4)
        self.assertNotIn('os.environ.get("XDG_DATA_HOME"', source)


if __name__ == "__main__":
    unittest.main()
