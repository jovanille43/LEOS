"""Unit tests for app-local controller navigation mapping."""

import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from controller_center.profiles import ControllerProfileStore
from gaming.backend.gamepad import GamepadActionMapper, mapper_from_preferences


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

    def test_held_dpad_direction_repeats_after_initial_delay(self):
        with patch("gaming.backend.gamepad.time.monotonic", return_value=10.0):
            self.assertEqual(
                self.mapper.feed(
                    {"kind": "button", "name": "BTN_DPAD_RIGHT", "value": 1}
                ),
                "right",
            )
        self.assertIsNone(self.mapper.repeat_action(now=10.37))
        self.assertEqual(self.mapper.repeat_action(now=10.38), "right")
        self.assertIsNone(self.mapper.repeat_action(now=10.49))
        self.assertEqual(self.mapper.repeat_action(now=10.51), "right")

    def test_releasing_direction_stops_repeat_without_extra_move(self):
        with patch("gaming.backend.gamepad.time.monotonic", return_value=20.0):
            self.assertEqual(
                self.mapper.feed(
                    {"kind": "axis", "name": "ABS_HAT0Y", "value": -1}
                ),
                "up",
            )
            self.assertIsNone(
                self.mapper.feed(
                    {"kind": "axis", "name": "ABS_HAT0Y", "value": 0}
                )
            )
        self.assertIsNone(self.mapper.repeat_action(now=21.0))

    def test_direction_change_restarts_initial_repeat_delay(self):
        with patch("gaming.backend.gamepad.time.monotonic", return_value=30.0):
            self.assertEqual(
                self.mapper.feed(
                    {"kind": "button", "name": "BTN_DPAD_LEFT", "value": 1}
                ),
                "left",
            )
        with patch("gaming.backend.gamepad.time.monotonic", return_value=30.5):
            self.assertEqual(
                self.mapper.feed(
                    {"kind": "button", "name": "BTN_DPAD_UP", "value": 1}
                ),
                "up",
            )
        self.assertIsNone(self.mapper.repeat_action(now=30.87))
        self.assertEqual(self.mapper.repeat_action(now=30.89), "up")

    def test_analog_stick_hold_repeats_and_returns_to_neutral(self):
        event = {
            "kind": "axis", "name": "ABS_X", "minimum": -1000,
            "maximum": 1000, "value": 700,
        }
        with patch("gaming.backend.gamepad.time.monotonic", return_value=40.0):
            self.assertEqual(self.mapper.feed(event), "right")
        self.assertEqual(self.mapper.repeat_action(now=40.38), "right")
        event["value"] = 0
        with patch("gaming.backend.gamepad.time.monotonic", return_value=40.5):
            self.assertIsNone(self.mapper.feed(event))
        self.assertIsNone(self.mapper.repeat_action(now=41.0))

    def test_reset_clears_held_directions_and_repeat_state(self):
        with patch("gaming.backend.gamepad.time.monotonic", return_value=50.0):
            self.assertEqual(
                self.mapper.feed(
                    {"kind": "button", "name": "BTN_DPAD_DOWN", "value": 1}
                ),
                "down",
            )
        self.mapper.reset()
        self.assertIsNone(self.mapper.repeat_action(now=51.0))
        with patch("gaming.backend.gamepad.time.monotonic", return_value=52.0):
            self.assertEqual(
                self.mapper.feed(
                    {"kind": "button", "name": "BTN_DPAD_UP", "value": 1}
                ),
                "up",
            )

    def test_nintendo_profile_swaps_confirm_and_back_buttons(self):
        mapper = GamepadActionMapper(profile="nintendo")
        self.assertEqual(
            mapper.feed({"kind": "button", "name": "BTN_EAST", "value": 1}),
            "confirm",
        )
        self.assertEqual(
            mapper.feed({"kind": "button", "name": "BTN_SOUTH", "value": 1}),
            "back",
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

    def test_saved_controller_profile_is_applied_to_gaming_navigation(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ControllerProfileStore(Path(directory) / "controllers.json")
            store.update(
                "test-controller",
                profile="nintendo",
                deadzone=15,
                axis_centers={"ABS_X": 100},
            )

            mapper = mapper_from_preferences(store.get("test-controller"))
            self.assertEqual(
                mapper.feed({"kind": "button", "name": "BTN_EAST", "value": 1}),
                "confirm",
            )
            self.assertEqual(
                mapper.feed({"kind": "button", "name": "BTN_SOUTH", "value": 1}),
                "back",
            )
            event = {
                "kind": "axis", "name": "ABS_X", "minimum": -900,
                "maximum": 1100, "value": 220,
            }
            self.assertIsNone(mapper.feed(event))
            event["value"] = 600
            self.assertEqual(mapper.feed(event), "right")

    def test_auto_profile_detects_nintendo_controller(self):
        mapper = mapper_from_preferences(
            {"profile": "auto", "deadzone": 8, "axis_centers": {}},
            {"name": "Switch Pro Controller", "vendor": 0x057E, "product": 0x2009},
        )
        self.assertEqual(
            mapper.feed({"kind": "button", "name": "BTN_SOUTH", "value": 1}),
            "back",
        )

    def test_auto_profile_uses_standard_layout_for_unknown_controller(self):
        mapper = mapper_from_preferences(
            {"profile": "auto"},
            {"name": "Generic Gamepad", "vendor": 0x1234, "product": 0x5678},
        )
        self.assertEqual(
            mapper.feed({"kind": "button", "name": "BTN_SOUTH", "value": 1}),
            "confirm",
        )

    def test_manual_profile_overrides_auto_detection(self):
        mapper = mapper_from_preferences(
            {"profile": "nintendo"},
            {"name": "DualSense", "vendor": 0x054C, "product": 0x0CE6},
        )
        self.assertEqual(
            mapper.feed({"kind": "button", "name": "BTN_SOUTH", "value": 1}),
            "back",
        )

    def test_malformed_axis_events_are_ignored_without_interrupting_navigation(self):
        malformed = [
            {"kind": "axis", "name": "ABS_HAT0X", "value": None},
            {"kind": "axis", "name": "ABS_HAT0Y", "value": "bad"},
            {"kind": "axis", "name": "ABS_X", "value": "bad"},
            {"kind": "axis", "name": "ABS_Y", "minimum": "bad", "value": 100},
            {"kind": "axis", "name": "ABS_X", "minimum": 10, "maximum": 10, "value": 10},
        ]
        for event in malformed:
            with self.subTest(event=event):
                self.assertIsNone(self.mapper.feed(event))
        self.assertEqual(
            self.mapper.feed({"kind": "button", "name": "BTN_SOUTH", "value": 1}),
            "confirm",
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
