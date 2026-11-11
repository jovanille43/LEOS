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

    def test_unknown_events_are_ignored(self):
        self.assertIsNone(
            self.mapper.feed({"kind": "button", "name": "BTN_TRIGGER", "value": 1})
        )
        self.assertIsNone(
            self.mapper.feed({"kind": "axis", "name": "ABS_X", "value": 300})
        )


if __name__ == "__main__":
    unittest.main()
