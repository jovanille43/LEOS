"""Regression test for concurrent dock-apply requests."""

from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from control_center.controller import ControlCenterController


class PlasmaApplyGuardTests(unittest.TestCase):
    def test_second_apply_is_rejected_before_inspecting_or_backing_up(self):
        controller = Mock()
        controller._plasma_layout_tasks = {"pending-backup": object()}
        controller.desktopLayout.get.return_value = {}
        controller.plasmaBackups.config_path = Path("/tmp/plasma-layout-test")

        with (
            patch("control_center.controller.inspect_plasma_config") as inspect,
            patch(
                "control_center.controller.build_layout_plan",
                return_value={"can_apply": False},
            ),
            patch(
                "control_center.controller.format_layout_report",
                return_value="Inspection normale",
            ),
        ):
            message = ControlCenterController.applyPlasmaLayout(controller, True)

        self.assertIn("déjà en cours", message.lower())
        inspect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
