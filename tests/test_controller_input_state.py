"""Tests for live button state in the controller center."""

import unittest

from controller_center.input_state import ControllerInputState


class ControllerInputStateTests(unittest.TestCase):
    def setUp(self):
        self.state = ControllerInputState()

    def test_pressed_buttons_are_reported_until_they_are_released(self):
        self.assertEqual(
            self.state.consume({"kind": "button", "name": "BTN_SOUTH", "value": 1}),
            "Bouton pressé : BTN_SOUTH",
        )
        self.assertEqual(self.state.buttons_text, "Maintenus : BTN_SOUTH")

        self.assertEqual(
            self.state.consume({"kind": "button", "name": "BTN_SOUTH", "value": 0}),
            "Bouton relâché : BTN_SOUTH",
        )
        self.assertEqual(self.state.buttons_text, "Aucun bouton maintenu.")

    def test_multiple_buttons_are_sorted_and_individually_released(self):
        self.state.consume({"kind": "button", "name": "BTN_EAST", "value": 1})
        self.state.consume({"kind": "button", "name": "BTN_SOUTH", "value": 1})
        self.assertEqual(
            self.state.pressed_buttons,
            ("BTN_EAST", "BTN_SOUTH"),
        )
        self.state.consume({"kind": "button", "name": "BTN_EAST", "value": 0})
        self.assertEqual(self.state.buttons_text, "Maintenus : BTN_SOUTH")

    def test_repeat_events_do_not_change_held_button_state(self):
        self.state.consume({"kind": "button", "name": "BTN_NORTH", "value": 1})
        self.assertIsNone(
            self.state.consume({"kind": "button", "name": "BTN_NORTH", "value": 2})
        )
        self.assertEqual(self.state.pressed_buttons, ("BTN_NORTH",))

    def test_axis_event_updates_last_event_without_changing_buttons(self):
        self.assertEqual(
            self.state.consume({"kind": "axis", "name": "ABS_X", "value": 123}),
            "Axe ABS_X : 123",
        )
        self.assertEqual(self.state.buttons_text, "Aucun bouton maintenu.")

    def test_invalid_events_are_ignored(self):
        self.assertIsNone(self.state.consume({"kind": "button", "name": "", "value": 1}))
        self.assertIsNone(self.state.consume({"kind": "button", "name": "BTN_SOUTH", "value": 3}))
        self.assertIsNone(self.state.consume({"kind": "other", "name": "BTN_SOUTH", "value": 1}))
        self.assertEqual(self.state.pressed_buttons, ())

    def test_controller_center_labels_the_live_held_button_list(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        qml = (root / "controller_center/qml/Main.qml").read_text(encoding="utf-8")
        controller = (root / "controller_center/controller.py").read_text(encoding="utf-8")
        self.assertIn('text: "BOUTONS MAINTENUS"', qml)
        self.assertIn("self.buttons_text = self.input_state.buttons_text", controller)

    def test_disconnect_clears_held_buttons(self):
        self.state.consume({"kind": "button", "name": "BTN_SOUTH", "value": 1})
        self.state.clear()
        self.assertEqual(self.state.pressed_buttons, ())
        self.assertEqual(self.state.buttons_text, "Aucun bouton maintenu.")


if __name__ == "__main__":
    unittest.main()
