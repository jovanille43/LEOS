"""Regression test for concurrent dock-apply requests."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PlasmaApplyGuardTests(unittest.TestCase):
    def test_second_apply_is_rejected_before_inspecting_or_backing_up(self):
        source = (ROOT / "control_center/controller.py").read_text(encoding="utf-8")
        start = source.index("    def applyPlasmaLayout(")
        end = source.index("    @Slot(str, bool, str)", start)
        method = source[start:end]
        guard = (
            'if self._plasma_layout_tasks:\n'
            '            return "Une application du dock est déjà en cours ; '
            'attends la fin avant de recommencer."'
        )

        self.assertIn(guard, method)
        self.assertLess(method.index(guard), method.index("inspect_plasma_config"))


if __name__ == "__main__":
    unittest.main()
