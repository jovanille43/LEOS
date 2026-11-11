"""Unit tests for app-local controller navigation mapping."""

import unittest

from gaming.backend.gamepad import GamepadActionMapper


class GamepadActionTests(unittest.TestCase):
    def setUp(self):
        self.mapper = GamepadActionMapper()

    def test_standard_buttons(self):
        self.assertEqual(
            self.mapper.feed({"kind": "button", "name": "BTN_SOUTH", "value": 1}),
            "confirm",
        )
        self.assertEqual(
            self.mapper.feed({"kind": "button", "name": "BTN_EAST", "value": 1}),
            "back",
        )
        self.assertEqual(
            self.mapper.feed({"kind": "button", "name": "BTN_START", "value": 1}),
            "menu",
        )

    def test_button_release_does_not_repeat_action(self):
        self.assertIsNone(
            self.mapper.feed({"kind": "button", "name": "BTN_SOUTH", "value": 0})
        )

    def test_hat_axis_emits_direction_and_releases_silently(self):
        self.assertEqual(
            self.mapper.feed({"kind": "axis", "name": "ABS_HAT0X", "value": -1}),
            "left",
        )
        self.assertIsNone(
            self.mapper.feed({"kind": "axis", "name": "ABS_HAT0X", "value": 0})
        )
        self.assertEqual(
            self.mapper.feed({"kind": "axis", "name": "ABS_HAT0Y", "value": 1}),
            "down",
        )

    def test_analog_stick_respects_deadzone(self):
        event = {"kind": "axis", "name": "ABS_X", "minimum": -1000, "maximum": 1000}
        event["value"] = 50
        self.assertIsNone(self.mapper.feed(event))
        event["value"] = 500
        self.assertEqual(self.mapper.feed(event), "right")
        event["value"] = 0
        self.assertIsNone(self.mapper.feed(event))

    def test_analog_stick_uses_saved_neutral_center(self):
        mapper = GamepadActionMapper(deadzone_percent=5, axis_centers={"ABS_Y": 100})
        event = {
            "kind": "axis", "name": "ABS_Y", "minimum": -900,
            "maximum": 1100, "value": 150,
        }
        self.assertIsNone(mapper.feed(event))
        event["value"] = 700
        self.assertEqual(mapper.feed(event), "down")

    def test_unknown_events_are_ignored(self):
        self.assertIsNone(
            self.mapper.feed({"kind": "button", "name": "BTN_TRIGGER", "value": 1})
        )
        self.assertIsNone(
            self.mapper.feed({"kind": "axis", "name": "ABS_X", "value": 300})
        )


if __name__ == "__main__":
    unittest.main()
