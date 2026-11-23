"""UI contracts for the live analog-stick view in Controller Center."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ControllerVisualPolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qml = (ROOT / "controller_center/qml/Main.qml").read_text(encoding="utf-8")
        cls.controller = (ROOT / "controller_center/controller.py").read_text(encoding="utf-8")

    def test_controller_center_exposes_both_live_stick_positions(self):
        for token in (
            "property var stickReadings: controllerCenter.stickVisuals",
            "STICKS ANALOGIQUES",
            "id: leftStickTrack",
            "id: rightStickTrack",
            "id: leftStickMarker",
            "id: rightStickMarker",
            "window.stickReadings.leftX",
            "window.stickReadings.leftY",
            "window.stickReadings.rightX",
            "window.stickReadings.rightY",
            "window.stickReadings.leftAvailable",
            "window.stickReadings.rightAvailable",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.qml)

    def test_raw_axis_diagnostics_and_accessible_status_remain_visible(self):
        self.assertIn("LECTURE DES CAPTEURS", self.qml)
        self.assertIn("controllerCenter.axesText", self.qml)
        self.assertIn("controllerCenter.lastEventText", self.qml)
        self.assertIn('text: controllerCenter.buttonsText', self.qml)
        self.assertIn('@Property("QVariantMap", notify=changed)', self.controller)
        self.assertIn("build_stick_visuals(self.backend.axes, self.backend.axis_ranges)", self.controller)


if __name__ == "__main__":
    unittest.main()
