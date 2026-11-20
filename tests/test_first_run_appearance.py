"""Tests for the consent-based LEOS Desktop first-run appearance transaction."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from desktop.branding_assets import source_asset_urls
from desktop.first_run_appearance import (
    APPLIED,
    PENDING,
    SKIPPED,
    DesktopAppearanceSetup,
)
from leos_core.settings import SettingsStore


class FakeBackups:
    config_path = Path("/fake/plasma-org.kde.plasma.desktop-appletsrc")

    def __init__(self):
        self.created = []
        self.restored = []

    def create_backup(self):
        self.created.append("backup-1")
        return "backup-12345678"

    def restore_backup(self, backup_id, *, confirmed=False):
        self.restored.append((backup_id, confirmed))
        return None


class FakeColors:
    def __init__(self):
        self.applied = []
        self.restored = 0
        self.available = True

    def tool_available(self):
        return self.available

    def current_scheme(self):
        return "BreezeDark"

    def apply_custom_theme(self, color_a, color_b, appearance="dark"):
        self.applied.append((color_a, color_b, appearance))
        return "applied"

    def can_restore(self):
        return bool(self.applied) and self.restored == 0

    def restore_previous_theme(self):
        self.restored += 1
        return "restored"


class FakeIcons:
    def __init__(self):
        self.applied = 0
        self.restored = 0
        self.available = True

    def tool_available(self):
        return self.available

    def theme_installed(self):
        return True

    def current_theme(self):
        return "breeze"

    def apply_theme(self, theme_id="leos"):
        self.applied += 1
        self.applied_ids = getattr(self, "applied_ids", []) + [theme_id]
        return "applied"

    def can_restore(self):
        return self.applied > self.restored

    def restore_previous_theme(self):
        self.restored += 1
        return "restored"


class FakeStyle:
    def __init__(self):
        self.applied = 0
        self.restored = 0
        self.available = True

    def tool_available(self):
        return self.available

    def style_installed(self):
        return True

    def current_style(self):
        return "Breeze"

    def apply_style(self, style_id="leos"):
        self.applied += 1
        self.applied_ids = getattr(self, "applied_ids", []) + [style_id]
        return "applied"

    def can_restore(self):
        return self.applied > self.restored

    def restore_previous_style(self):
        self.restored += 1
        return "restored"


class FakeLayout:
    def get(self):
        return {
            "schema_version": 1,
            "profile": "leos-default",
            "dock": {
                "enabled": True,
                "position": "bottom",
                "alignment": "center",
                "auto_hide": False,
            },
            "widgets_enabled": False,
        }


class FakeFavourites:
    def __init__(self, valid=True):
        self.valid = valid

    def load(self):
        return self.valid

    def items(self):
        return ["leos-menu.desktop", "org.kde.dolphin.desktop", "steam.desktop"]


class DesktopAppearanceSetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = SettingsStore(Path(self.temp.name) / "settings.json")
        self.settings.set_many({
            "theme_color_a": "#FF8800",
            "theme_color_b": "#0055CC",
            "theme_colors_configured": True,
        })
        self.backups = FakeBackups()
        self.colors = FakeColors()
        self.style = FakeStyle()
        self.icons = FakeIcons()
        self.layout = FakeLayout()
        self.favourites = FakeFavourites()
        self.wallpaper = Path(self.temp.name) / "desktop-leos.svg"
        self.wallpaper.write_text("<svg/>", encoding="utf-8")
        self.scripts = []
        self.brand_asset_calls = []
        self.plasma_resource_calls = []

        def build_plasma_resources(color_a, color_b):
            self.plasma_resource_calls.append((color_a, color_b))
            return {"plasmaStyleId": "leos-custom-test", "iconThemeId": "leos-custom-test"}

        def build_assets(color_a, color_b):
            self.brand_asset_calls.append((color_a, color_b))
            return {"desktopWallpaperUrl": "file:///cache/desktop-custom.svg"}

        def execute(script, *, timeout):
            self.scripts.append((script, timeout))
            return True, "La commande a été acceptée par Plasma."

        self.setup = DesktopAppearanceSetup(
            settings=self.settings,
            backups=self.backups,
            colors=self.colors,
            style=self.style,
            icons=self.icons,
            layout=self.layout,
            favourites=self.favourites,
            wallpaper=self.wallpaper,
            command_lookup=lambda name: "/usr/bin/" + name,
            script_executor=execute,
            branding_asset_builder=build_assets,
            plasma_resource_builder=build_plasma_resources,
        )

    def tearDown(self):
        self.temp.cleanup()

    @patch("desktop.first_run_appearance.inspect_plasma_config", return_value={"available": True})
    @patch("desktop.first_run_appearance.build_layout_plan", return_value={"can_apply": True})
    @patch("desktop.first_run_appearance.build_panel_management_script", return_value="plasma-script")
    def test_apply_runs_backed_up_profile_and_marks_it_complete(self, *_mocks):
        message = self.setup.apply()
        self.assertEqual(self.settings.get("desktop_appearance_setup"), APPLIED)
        self.assertEqual(self.backups.created, ["backup-1"])
        self.assertEqual(self.colors.applied, [("#FF8800", "#0055CC", "dark")])
        self.assertEqual(self.brand_asset_calls, [("#FF8800", "#0055CC")])
        self.assertEqual(self.style.applied, 1)
        self.assertEqual(self.style.applied_ids, ["leos-custom-test"])
        self.assertEqual(self.icons.applied, 1)
        self.assertEqual(self.icons.applied_ids, ["leos-custom-test"])
        self.assertEqual(self.plasma_resource_calls, [("#FF8800", "#0055CC")])
        self.assertEqual(self.scripts, [("plasma-script", 30.0)])
        self.assertIn("sauvegarde", message.lower())

    def test_custom_pair_must_be_explicitly_configured_before_any_change(self):
        self.settings.set("theme_colors_configured", False)
        with self.assertRaisesRegex(RuntimeError, "deux couleurs A et B"):
            self.setup.apply()
        self.assertEqual(self.backups.created, [])
        self.assertEqual(self.colors.applied, [])
        self.assertEqual(self.brand_asset_calls, [])
        self.assertEqual(self.plasma_resource_calls, [])
        self.assertEqual(self.settings.get("desktop_appearance_setup"), PENDING)

    def test_custom_plasma_resource_generation_failure_aborts_before_backup(self):
        self.setup.plasma_resource_builder = lambda color_a, color_b: (_ for _ in ()).throw(
            FileNotFoundError("generated theme sources missing")
        )
        with self.assertRaisesRegex(RuntimeError, "generated theme sources missing"):
            self.setup.apply()
        self.assertEqual(self.backups.created, [])
        self.assertEqual(self.colors.applied, [])
        self.assertEqual(self.style.applied, 0)
        self.assertEqual(self.icons.applied, 0)
        self.assertEqual(self.settings.get("desktop_appearance_setup"), PENDING)

    @patch("desktop.first_run_appearance.inspect_plasma_config", return_value={"available": True})
    @patch("desktop.first_run_appearance.build_layout_plan", return_value={"can_apply": True})
    def test_custom_wallpaper_generation_failure_aborts_before_kde_changes(self, *_mocks):
        self.setup.branding_asset_builder = lambda color_a, color_b: {
            "desktopWallpaperUrl": source_asset_urls()["desktopWallpaperUrl"]
        }
        with self.assertRaisesRegex(RuntimeError, "fond personnalisé A/B"):
            self.setup.apply()
        self.assertEqual(self.backups.created, [])
        self.assertEqual(self.colors.applied, [])
        self.assertEqual(self.style.applied, 0)
        self.assertEqual(self.icons.applied, 0)
        self.assertEqual(self.settings.get("desktop_appearance_setup"), PENDING)

    def test_explicit_skip_is_persisted_and_apply_is_not_started(self):
        self.assertEqual(self.setup.skip(), SKIPPED)
        self.assertEqual(self.settings.get("desktop_appearance_setup"), SKIPPED)
        with self.assertRaises(RuntimeError):
            self.setup.apply()
        self.assertEqual(self.backups.created, [])
        self.assertEqual(self.colors.applied, [])

    @patch("desktop.first_run_appearance.inspect_plasma_config", return_value={"available": True})
    @patch(
        "desktop.first_run_appearance.build_layout_plan",
        return_value={"can_apply": False, "blocked_reason": "Plusieurs panneaux KDE sont présents."},
    )
    def test_unsafe_multi_panel_layout_is_blocked_before_any_change(self, *_mocks):
        with self.assertRaisesRegex(RuntimeError, "Plusieurs panneaux KDE"):
            self.setup.apply()
        self.assertEqual(self.backups.created, [])
        self.assertEqual(self.colors.applied, [])
        self.assertEqual(self.style.applied, 0)
        self.assertEqual(self.settings.get("desktop_appearance_setup"), PENDING)

    @patch("desktop.first_run_appearance.inspect_plasma_config", return_value={"available": True})
    @patch("desktop.first_run_appearance.build_layout_plan", return_value={"can_apply": True})
    @patch("desktop.first_run_appearance.build_panel_management_script", return_value="plasma-script")
    def test_script_failure_restores_plasma_backup_style_and_colors(self, *_mocks):
        self.setup.script_executor = lambda script, *, timeout: (False, "Plasma a refusé le profil.")
        with self.assertRaisesRegex(RuntimeError, "réglages précédents ont été restaurés"):
            self.setup.apply()
        self.assertEqual(self.backups.restored, [("backup-12345678", True)])
        self.assertEqual(self.style.restored, 1)
        self.assertEqual(self.icons.restored, 1)
        self.assertEqual(self.colors.restored, 1)
        self.assertEqual(self.settings.get("desktop_appearance_setup"), PENDING)

    def test_invalid_saved_favourites_block_before_backup(self):
        self.favourites.valid = False
        with self.assertRaisesRegex(RuntimeError, "favoris du dock"):
            self.setup.apply()
        self.assertEqual(self.backups.created, [])
        self.assertEqual(self.colors.applied, [])
        self.assertEqual(self.style.applied, 0)
        self.assertEqual(self.icons.applied, 0)

    def test_missing_icon_theme_tool_blocks_before_backup(self):
        self.icons.available = False
        with self.assertRaisesRegex(FileNotFoundError, "thème d'icônes"):
            self.setup.apply()
        self.assertEqual(self.backups.created, [])
        self.assertEqual(self.colors.applied, [])
        self.assertEqual(self.style.applied, 0)

    def test_missing_required_command_blocks_before_backup(self):
        self.setup.command_lookup = lambda name: None
        with self.assertRaisesRegex(FileNotFoundError, "busctl"):
            self.setup.apply()
        self.assertEqual(self.backups.created, [])


if __name__ == "__main__":
    unittest.main()
