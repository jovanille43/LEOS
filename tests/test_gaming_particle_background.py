"""Source contracts for the LEOS Gaming animated A/B particle backdrop."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class GamingParticleBackgroundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        cls.field = (ROOT / "gaming/qml/ParticleField.qml").read_text(encoding="utf-8")

    def test_particle_field_uses_live_user_selected_a_and_b_colors(self):
        self.assertIn("property color colorA", self.field)
        self.assertIn("property color colorB", self.field)
        self.assertIn("index % 2 === 0 ? root.colorA : root.colorB", self.field)
        self.assertIn("colorA: window.accentA", self.main)
        self.assertIn("colorB: window.accentB", self.main)

    def test_particles_drift_and_pulse_slowly_without_video_wallpaper_assets(self):
        self.assertIn("Repeater", self.field)
        self.assertIn("NumberAnimation", self.field)
        self.assertIn("loops: Animation.Infinite", self.field)
        self.assertIn("Easing.InOutSine", self.field)
        self.assertIn("travelDuration: 23000", self.field)
        self.assertNotIn("QtMultimedia", self.field)
        self.assertNotIn("Video", self.field)

    def test_particle_motion_respects_leos_animation_preference(self):
        self.assertIn("active: leos.animationsEnabled && !window.returningToDesktop", self.main)
        self.assertIn("running: root.active", self.field)

    def test_particle_layer_is_behind_the_gaming_interface(self):
        content_start = self.main.index("id: gamingContent")
        particles = self.main.index("ParticleField {", content_start)
        content = self.main.index("ColumnLayout {", particles)
        self.assertLess(particles, content)
        self.assertIn("anchors.fill: parent", self.main[particles:content])
        self.assertIn("z: 0", self.main[particles:content])

    def test_particle_count_is_bounded_for_different_screen_sizes(self):
        self.assertIn(
            "particleCount: Math.min(52, Math.max(30, Math.floor(window.width / 32)))",
            self.main,
        )


if __name__ == "__main__":
    unittest.main()
