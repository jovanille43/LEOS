"""Integration checks for the selected-game artwork presentation."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class GamingArtworkIntegrationTests(unittest.TestCase):
    def test_library_exposes_only_discovered_local_artwork(self):
        source = (ROOT / "gaming/backend/library.py").read_text(encoding="utf-8")
        self.assertIn('"artwork": str(game.get("artwork", ""))', source)

    def test_qml_passes_artwork_through_game_selection(self):
        source = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn('property string selectedArtwork = ""', source)
        self.assertIn('info.favorite, info.artwork)', source)
        self.assertIn('source: window.selectedArtwork', source)
        self.assertIn('window.selectedArtwork.length === 0', source)

    def test_missing_artwork_has_an_explicit_fallback(self):
        source = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn('ARTWORK NON DISPONIBLE', source)
        self.assertIn('SÉLECTIONNE UN JEU', source)


if __name__ == "__main__":
    unittest.main()
