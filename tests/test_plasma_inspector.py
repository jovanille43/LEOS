"""Tests for the read-only KDE Plasma inspector and LEOS plan preview."""
import tempfile
import unittest
from pathlib import Path

from desktop.layouts import DesktopLayoutStore
from desktop.plasma_inspector import build_layout_plan, inspect_plasma_config, format_layout_report


PLASMA_CONFIG = """[Containments][1]
plugin=org.kde.plasma.panel
location=4
formfactor=2

[Containments][1][Applets][7]
plugin=org.kde.plasma.digitalclock

[Containments][1][Applets][9]
plugin=org.kde.plasma.systemtray

[Containments][2]
plugin=org.kde.plasma.desktop
location=0
formfactor=0
"""


class PlasmaInspectorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "plasma-org.kde.plasma.desktop-appletsrc"
        self.path.write_text(PLASMA_CONFIG, encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    def test_detects_panels_and_applets(self):
        result = inspect_plasma_config(self.path)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["containment_count"], 2)
        self.assertEqual(result["panel_count"], 1)
        self.assertEqual(result["panels"][0]["id"], "1")
        self.assertEqual(result["panels"][0]["location"], "4")
        self.assertEqual(
            [item["plugin"] for item in result["panels"][0]["applets"]],
            ["org.kde.plasma.digitalclock", "org.kde.plasma.systemtray"],
        )

    def test_detects_leos_owned_panel_marker(self):
        self.path.write_text(
            PLASMA_CONFIG + "\n[Containments][1][LEOS]\nmanagedBy=leos-panel-v1\n",
            encoding="utf-8",
        )
        result = inspect_plasma_config(self.path)
        self.assertTrue(result["panels"][0]["leos_managed"])

    def test_unmarked_existing_panel_is_reported_as_personal(self):
        result = inspect_plasma_config(self.path)
        self.assertFalse(result["panels"][0]["leos_managed"])
        store = DesktopLayoutStore(self.path.parent / "desktop-layout.json")
        plan = build_layout_plan(store.get(), result)
        self.assertTrue(any("panneau(x) KDE personnel(s)" in item for item in plan["observations"]))

    def test_inspection_is_read_only(self):
        before = self.path.read_bytes()
        inspect_plasma_config(self.path)
        self.assertEqual(self.path.read_bytes(), before)

    def test_plan_is_preview_only_and_respects_requested_layout(self):
        store = DesktopLayoutStore(self.path.parent / "desktop-layout.json")
        store.apply_profile("minimal")
        inspection = inspect_plasma_config(self.path)
        plan = build_layout_plan(store.get(), inspection)
        self.assertEqual(plan["mode"], "preview-only")
        self.assertFalse(plan["can_apply"])
        self.assertTrue(plan["requires_backup"])
        self.assertTrue(plan["desired"]["dock"]["auto_hide"])
        self.assertEqual(plan["detected_panel_count"], 1)

    def test_plan_does_not_claim_to_remove_existing_panels(self):
        store = DesktopLayoutStore(self.path.parent / "desktop-layout.json")
        store.set_dock(enabled=False)
        plan = build_layout_plan(store.get(), inspect_plasma_config(self.path))
        self.assertFalse(plan["can_apply"])
        self.assertIn("ne seront pas supprimés", plan["observations"][0])

    def test_missing_config_is_reported(self):
        result = inspect_plasma_config(self.path.with_name("missingrc"))
        self.assertEqual(result["status"], "missing")
        self.assertFalse(result["available"])

    def test_invalid_ini_is_reported(self):
        self.path.write_text("this is not an ini file", encoding="utf-8")
        result = inspect_plasma_config(self.path)
        self.assertEqual(result["status"], "invalid")

    def test_symlink_is_not_followed(self):
        link = self.path.with_name("plasma-link")
        link.symlink_to(self.path)
        result = inspect_plasma_config(link)
        self.assertEqual(result["status"], "unsafe")
        self.assertFalse(result["available"])

    def test_control_center_exposes_inspection_but_not_apply(self):
        root = Path(__file__).resolve().parents[1]
        controller = (root / "control_center" / "controller.py").read_text(encoding="utf-8")
        qml = (root / "control_center" / "qml" / "Main.qml").read_text(encoding="utf-8")
        self.assertIn("def inspectPlasmaLayout(self)", controller)
        self.assertIn("controlCenter.inspectPlasmaLayout()", qml)
        self.assertIn("INSPECTION DU BUREAU KDE", qml)
        self.assertNotIn("applyPlasmaLayout", controller + qml)

    def test_report_explains_read_only_state(self):
        result = inspect_plasma_config(self.path)
        store = DesktopLayoutStore(self.path.parent / "desktop-layout.json")
        report = format_layout_report(result, build_layout_plan(store.get(), result))
        self.assertIn("LECTURE SEULE", report)
        self.assertIn("Aucune modification", report)
        self.assertIn("Panneau 1", report)


if __name__ == "__main__":
    unittest.main()
