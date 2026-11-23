"""Regression checks for the Desktop/Gaming handoff transition."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ModeTransitionPolishTests(unittest.TestCase):
    def test_gaming_handoff_crossfades_intro_into_the_branded_loading_cover(self):
        qml = (ROOT / "launcher/qml/ModeSelector.qml").read_text(encoding="utf-8")
        self.assertIn("id: introHandoffCrossfade", qml)
        self.assertIn("ParallelAnimation", qml)
        self.assertIn("target: introVideoOutput", qml)
        self.assertIn("target: introHandoffScreen", qml)
        self.assertIn("duration: 260", qml)
        self.assertIn("introHandoffCrossfade.start()", qml)
        self.assertIn("onFinished: introVideoOutput.visible = false", qml)

    def test_failed_or_cancelled_handoff_restores_the_selector_overlay_state(self):
        qml = (ROOT / "launcher/qml/ModeSelector.qml").read_text(encoding="utf-8")
        self.assertIn("introHandoffCrossfade.stop()", qml)
        self.assertIn("introHandoffScreen.opacity = 0", qml)
        self.assertIn("introVideoOutput.opacity = 1", qml)
        self.assertIn("introOverlay.visible = false", qml)
        self.assertIn("if (transitionInProgress)", qml)


if __name__ == "__main__":
    unittest.main()
