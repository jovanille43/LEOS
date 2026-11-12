"""Tests for safe Plasma JavaScript adapter generation."""
import unittest

from desktop.layouts import DesktopLayoutStore
from desktop.plasma_adapter import (
    LEOS_PANEL_MARKER,
    PANEL_WIDGETS,
    adapter_capabilities,
    build_panel_management_script,
)


class PlasmaAdapterTests(unittest.TestCase):
    def setUp(self):
        self.store = DesktopLayoutStore()

    def test_generates_plasma_script_from_saved_layout(self):
        self.store.apply_profile("minimal")
        script = build_panel_management_script(self.store.get())
        self.assertIn('"enabled":true', script)
        self.assertIn('"autoHide":true', script)
        self.assertIn('panel.location = desired.position', script)
        self.assertIn('panel.hiding = desired.autoHide ? "autohide" : "none"', script)
        self.assertIn('panel.lengthMode = "fit"', script)

    def test_script_uses_leos_ownership_marker(self):
        script = build_panel_management_script(self.store.get())
        self.assertIn(LEOS_PANEL_MARKER, script)
        self.assertIn('candidate.readConfig("managedBy", "")', script)
        self.assertIn('panel.writeConfig("managedBy", markerValue)', script)

    def test_script_adopts_only_one_panel_and_keeps_its_existing_applets(self):
        script = build_panel_management_script(self.store.get())
        self.assertIn('if (isLeosPanel(allPanels[i]))', script)
        self.assertIn('var panel = existing.length === 1 ? existing[0] : null', script)
        self.assertIn('else if (allPanels.length === 1)', script)
        self.assertIn('panel.widgets(essentialWidgets[e]).length === 0', script)
        self.assertIn('panel.writeConfig("managedBy", markerValue)', script)
        self.assertIn('addedWidgets[r].remove()', script)

    def test_script_checks_widget_availability_before_panel_creation(self):
        script = build_panel_management_script(self.store.get())
        for widget in PANEL_WIDGETS:
            self.assertIn(widget, script)
        self.assertIn('availableTypes.indexOf(widgetTypes[a])', script)
        self.assertIn('widgetsToAdd.length < 2', script)

    def test_failed_creation_removes_only_the_panel_created_by_that_script(self):
        script = build_panel_management_script(self.store.get())
        created_branch = script.index("if (created && panel)")
        remove_call = script.index("panel.remove()")
        existing_panel_rollback = script.index("} else if (panel && before)")
        self.assertLess(created_branch, remove_call)
        self.assertLess(remove_call, existing_panel_rollback)
        self.assertEqual(script.count("panel.remove()"), 1)
        self.assertIn("LEOS_PARTIAL_PANEL_ROLLED_BACK=1", script)
        self.assertNotIn("LEOS_PARTIAL_PANEL_HIDDEN_FOR_MANUAL_REVIEW=1", script)

    def test_disabling_dock_refuses_to_remove_any_panel(self):
        self.store.set_dock(enabled=False)
        script = build_panel_management_script(self.store.get())
        disable_start = script.index("if (!desired.enabled)")
        disable_end = script.index("if (desired.widgetsEnabled)", disable_start)
        disable_branch = script[disable_start:disable_end]
        self.assertIn("throw new Error", disable_branch)
        self.assertNotIn(".remove()", disable_branch)

    def test_script_requires_plasma_six_or_newer(self):
        script = build_panel_management_script(self.store.get())
        self.assertIn('versionMajor < 6', script)
        self.assertIn('applicationVersion', script)

    def test_script_avoids_unsupported_floating_property(self):
        script = build_panel_management_script(self.store.get())
        self.assertNotIn("panel.floating", script)

    def test_script_contains_rollback_for_existing_panel_properties(self):
        script = build_panel_management_script(self.store.get())
        self.assertIn('panel.location = before.location', script)
        self.assertIn('panel.alignment = before.alignment', script)

    def test_invalid_layout_is_rejected(self):
        with self.assertRaises(ValueError):
            build_panel_management_script({"profile": "invalid"})

    def test_capabilities_are_honest_about_runtime_validation(self):
        capabilities = adapter_capabilities()
        self.assertTrue(capabilities["touches_unmanaged_panels"])
        self.assertTrue(capabilities["adopts_single_unmanaged_panel_with_backup"])
        self.assertFalse(capabilities["can_remove_leos_owned_dock"])
        self.assertFalse(capabilities["desktop_widgets_applied"])
        self.assertFalse(capabilities["runtime_validated_on_bazzite"])
        self.assertTrue(capabilities["requires_backup_and_explicit_confirmation"])


if __name__ == "__main__":
    unittest.main()
