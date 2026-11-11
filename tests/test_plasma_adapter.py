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
        self.assertIn('panel.readConfig("managedBy", "")', script)
        self.assertIn('panel.remove()', script)

    def test_script_does_not_adopt_or_remove_unmanaged_panels(self):
        script = build_panel_management_script(self.store.get())
        self.assertIn('if (isLeosPanel(allPanels[i]))', script)
        self.assertIn('var panel = existing.length === 1 ? existing[0] : null', script)
        self.assertIn('panel = new Panel()', script)
        self.assertNotIn('allPanels[0].remove()', script)

    def test_script_checks_widget_availability_and_avoids_duplicates(self):
        script = build_panel_management_script(self.store.get())
        for widget in PANEL_WIDGETS:
            self.assertIn(widget, script)
        self.assertIn('availableTypes.indexOf(widgetType)', script)
        self.assertIn('currentTypes.indexOf(widgetType)', script)

    def test_script_contains_rollback_for_existing_or_new_panel(self):
        script = build_panel_management_script(self.store.get())
        self.assertIn('if (created && panel)', script)
        self.assertIn('panel.location = before.location', script)
        self.assertIn('addedWidgets[r].remove()', script)

    def test_disabling_dock_removes_only_marked_leos_panel(self):
        self.store.set_dock(enabled=False)
        script = build_panel_management_script(self.store.get())
        self.assertIn('if (!desired.enabled)', script)
        self.assertIn('if (panel) {\n            panel.remove();', script)
        self.assertIn('LEOS_PANEL_ALREADY_ABSENT', script)

    def test_invalid_layout_is_rejected(self):
        with self.assertRaises(ValueError):
            build_panel_management_script({"profile": "invalid"})

    def test_capabilities_are_honest_about_runtime_validation(self):
        capabilities = adapter_capabilities()
        self.assertFalse(capabilities["touches_unmanaged_panels"])
        self.assertFalse(capabilities["desktop_widgets_applied"])
        self.assertFalse(capabilities["runtime_validated_on_bazzite"])
        self.assertTrue(capabilities["requires_backup_and_explicit_confirmation"])


if __name__ == "__main__":
    unittest.main()
