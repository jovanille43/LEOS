"""Tests for explicit LEOS Plasma Style application and rollback."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from desktop.plasma_style import PlasmaStyleManager, MANAGED_BY, STYLE_ID


class FakeRunner:
    def __init__(self, returncode=0):
        self.returncode = returncode
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        return SimpleNamespace(returncode=self.returncode, stderr="fake failure")


class PlasmaStyleManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.data = root / "data"
        self.config = root / "config"
        self.state = root / "state"
        self.system = root / "system-themes"
        self.config.mkdir()
        self.system.mkdir()
        self.theme = self.system / STYLE_ID
        self.theme.mkdir()
        (self.theme / "metadata.json").write_text(
            json.dumps({"KPlugin": {"Id": STYLE_ID, "Name": "LEOS"}}),
            encoding="utf-8",
        )
        (self.config / "plasmarc").write_text(
            "[Theme]\nname=breeze-dark\n", encoding="utf-8"
        )
        self.runner = FakeRunner()
        self.manager = PlasmaStyleManager(
            self.data, self.config, self.state, self.system,
            "/usr/bin/plasma-apply-desktoptheme", self.runner,
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_detects_packaged_style(self):
        self.assertTrue(self.manager.style_installed())

    def test_reads_current_style_without_modifying_config(self):
        before = (self.config / "plasmarc").read_text(encoding="utf-8")
        self.assertEqual(self.manager.current_style(), "breeze-dark")
        self.assertEqual((self.config / "plasmarc").read_text(encoding="utf-8"), before)

    def test_apply_runs_fixed_style_without_shell_and_saves_rollback(self):
        self.assertIn("appliqué", self.manager.apply_style())
        args, kwargs = self.runner.calls[0]
        self.assertEqual(args, ["/usr/bin/plasma-apply-desktoptheme", "leos"])
        self.assertFalse(kwargs["shell"])
        self.assertTrue(self.manager.can_restore())
        self.assertFalse(self.manager._read_state()["apply_pending"])
        self.assertEqual(self.manager._read_state()["managed_by"], MANAGED_BY)
        self.assertEqual(self.manager.state_file.stat().st_mode & 0o777, 0o600)

    def test_restore_uses_previous_style_and_clears_state(self):
        self.manager.apply_style()
        self.assertIn("breeze-dark", self.manager.restore_previous_style())
        self.assertEqual(self.runner.calls[-1][0], [
            "/usr/bin/plasma-apply-desktoptheme", "breeze-dark"
        ])
        self.assertFalse(self.manager.can_restore())

    def test_repeated_apply_keeps_original_rollback_target(self):
        self.manager.apply_style()
        (self.config / "plasmarc").write_text("[Theme]\nname=leos\n", encoding="utf-8")
        self.manager.apply_style()
        self.assertEqual(self.manager._read_state()["previous_style"], "breeze-dark")

    def test_refuses_when_active_style_is_unknown(self):
        (self.config / "plasmarc").write_text("[Theme]\n", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            self.manager.apply_style()
        self.assertEqual(self.runner.calls, [])

    def test_refuses_when_package_is_missing(self):
        (self.theme / "metadata.json").unlink()
        with self.assertRaises(FileNotFoundError):
            self.manager.apply_style()
        self.assertEqual(self.runner.calls, [])

    def test_failed_apply_keeps_rollback_target(self):
        self.runner.returncode = 1
        with self.assertRaises(RuntimeError):
            self.manager.apply_style()
        self.assertTrue(self.manager.can_restore())
        self.assertTrue(self.manager._read_state()["apply_pending"])

    def test_refuses_corrupt_existing_state_without_overwriting(self):
        self.state.mkdir()
        target = self.state / "leos"
        target.mkdir()
        state_file = target / "plasma-style.json"
        state_file.write_text("{broken", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.manager.apply_style()
        self.assertEqual(state_file.read_text(encoding="utf-8"), "{broken")

    def test_control_center_wires_apply_and_restore_with_confirmation(self):
        root = Path(__file__).resolve().parents[1]
        controller = (root / "control_center" / "controller.py").read_text(encoding="utf-8")
        qml = (root / "control_center" / "qml" / "Main.qml").read_text(encoding="utf-8")
        self.assertIn("PlasmaStyleManager()", controller)
        self.assertIn("def applyPlasmaStyle(self)", controller)
        self.assertIn("def restorePreviousPlasmaStyle(self)", controller)
        self.assertIn("plasmaStyleConfirmation.open()", qml)
        self.assertIn("controlCenter.applyPlasmaStyle()", qml)
        self.assertIn("controlCenter.restorePreviousPlasmaStyle()", qml)


if __name__ == "__main__":
    unittest.main()
