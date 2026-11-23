"""Tests for normalized live analog-stick positions."""

import unittest

from controller_center.axis_visuals import build_stick_visuals


class StickVisualTests(unittest.TestCase):
    def test_both_sticks_are_normalized_from_their_hardware_ranges(self):
        visuals = build_stick_visuals(
            {
                "ABS_X": 50, "ABS_Y": -50,
                "ABS_RX": 0, "ABS_RY": 100,
            },
            {
                "ABS_X": {"minimum": -100, "maximum": 100},
                "ABS_Y": {"minimum": -100, "maximum": 100},
                "ABS_RX": {"minimum": -200, "maximum": 200},
                "ABS_RY": {"minimum": -100, "maximum": 300},
            },
        )
        self.assertTrue(visuals["leftAvailable"])
        self.assertTrue(visuals["rightAvailable"])
        self.assertEqual(visuals["leftX"], 0.5)
        self.assertEqual(visuals["leftY"], -0.5)
        self.assertEqual(visuals["rightX"], 0.0)
        self.assertEqual(visuals["rightY"], 0.0)

    def test_missing_axes_keep_the_marker_centered_and_mark_stick_unavailable(self):
        visuals = build_stick_visuals(
            {"ABS_X": 32767},
            {"ABS_X": {"minimum": -32768, "maximum": 32767}},
        )
        self.assertFalse(visuals["leftAvailable"])
        self.assertFalse(visuals["rightAvailable"])
        self.assertEqual(visuals["leftX"], 1.0)
        self.assertEqual(visuals["leftY"], 0.0)
        self.assertEqual(visuals["rightX"], 0.0)
        self.assertEqual(visuals["rightY"], 0.0)

    def test_values_are_clamped_to_the_visual_track(self):
        visuals = build_stick_visuals(
            {"ABS_X": 900, "ABS_Y": -900},
            {
                "ABS_X": {"minimum": -100, "maximum": 100},
                "ABS_Y": {"minimum": -100, "maximum": 100},
            },
        )
        self.assertEqual(visuals["leftX"], 1.0)
        self.assertEqual(visuals["leftY"], -1.0)

    def test_degenerate_or_invalid_ranges_are_reported_as_unavailable(self):
        visuals = build_stick_visuals(
            {"ABS_X": 10, "ABS_Y": "not-a-number"},
            {
                "ABS_X": {"minimum": 10, "maximum": 10},
                "ABS_Y": {"minimum": -1, "maximum": 1},
            },
        )
        self.assertFalse(visuals["leftAvailable"])
        self.assertEqual(visuals["leftX"], 0.0)
        self.assertEqual(visuals["leftY"], 0.0)

    def test_neutral_positions_are_near_the_center(self):
        visuals = build_stick_visuals(
            {"ABS_X": 0, "ABS_Y": 0},
            {
                "ABS_X": {"minimum": -32768, "maximum": 32767},
                "ABS_Y": {"minimum": -32768, "maximum": 32767},
            },
        )
        self.assertTrue(visuals["leftAvailable"])
        self.assertAlmostEqual(visuals["leftX"], 0.0, places=3)
        self.assertAlmostEqual(visuals["leftY"], 0.0, places=3)


if __name__ == "__main__":
    unittest.main()
