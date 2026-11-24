"""Cross-screen design-system contracts for LEOS visual consistency."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LeosVisualSystemTests(unittest.TestCase):
    def test_desktop_and_gaming_keep_a_shared_surface_language(self):
        desktop = (ROOT / "desktop/qml/Menu.qml").read_text(encoding="utf-8")
        gaming = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        for source in (desktop, gaming):
            self.assertIn("window.themeColors.surface", source)
            self.assertIn("window.themeColors.surface_elevated", source)
            self.assertIn("window.themeColors.border", source)
            self.assertIn("GradientStop { position: 0; color: window.accentA }", source)
            self.assertIn("GradientStop { position: 1; color: window.accentB }", source)

    def test_gaming_particle_twinkle_respects_reduced_motion(self):
        gaming = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        atmosphere = gaming.split("id: gamingContent", 1)[1].split("ColumnLayout {", 1)[0]
        self.assertIn("SequentialAnimation {", atmosphere)
        self.assertIn("running: leos.animationsEnabled", atmosphere)
        self.assertIn('property: "opacity"', atmosphere)
        self.assertIn("baseOpacity", atmosphere)

    def test_gaming_particles_drift_inside_their_screen_positions(self):
        gaming = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        atmosphere = gaming.split("id: gamingContent", 1)[1].split("ColumnLayout {", 1)[0]
        self.assertIn("property real baseX:", atmosphere)
        self.assertIn("property real baseY:", atmosphere)
        self.assertIn("property real driftX:", atmosphere)
        self.assertIn("property real driftY:", atmosphere)
        self.assertIn('property: "x"', atmosphere)
        self.assertIn('property: "y"', atmosphere)

    def test_mode_selector_reports_first_run_status_and_remembers_mode_choice(self):
        selector = (ROOT / "launcher/qml/ModeSelector.qml").read_text(encoding="utf-8")
        for status in (
            "IDENTITÉ A/B",
            "GUIDE DE BIENVENUE",
            "PROFIL DESKTOP",
            "IGNORÉE À TA DEMANDE",
            "firstRunCompletedCount",
        ):
            self.assertIn(status, selector)
        mode_request = selector.split("function requestModeWithIntro(mode)", 1)[1].split(
            "function finishModeTransition()", 1
        )[0]
        self.assertIn("modeSelectorController.completeOnboarding()", mode_request)

    def test_operational_screens_use_the_same_subtle_ab_highlight(self):
        screens = [
            "control_center/qml/Main.qml",
            "controller_center/qml/Main.qml",
            "desktop/qml/Notifications.qml",
        ]
        for path in screens:
            source = (ROOT / path).read_text(encoding="utf-8")
            self.assertIn("window.accentA", source)
            self.assertIn("window.accentB", source)
            self.assertIn("window.themeColors.surface", source)
            self.assertIn("window.themeColors.border", source)

    def test_notifications_and_library_artwork_have_semantic_fallbacks(self):
        notifications = (ROOT / "desktop/qml/Notifications.qml").read_text(encoding="utf-8")
        gaming = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn('visible: !isRead', notifications)
        self.assertIn("gameArtwork.status !== Image.Ready", gaming)
        self.assertIn("window.gameMonogram(gameCard.title)", gaming)


if __name__ == "__main__":
    unittest.main()
