"""Source-contract tests for the Gaming library visual polish."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class GamingLibraryVisualTests(unittest.TestCase):
    def test_missing_card_artwork_uses_a_title_monogram(self):
        source = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("function gameMonogram(title)", source)
        self.assertIn("text: window.gameMonogram(gameCard.title)", source)
        self.assertIn("visible: gameCard.artwork.length === 0", source)

    def test_card_artwork_fades_in_and_selection_transitions(self):
        source = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("Behavior on opacity { NumberAnimation { duration: 180 } }", source)
        self.assertIn("Behavior on border.color { ColorAnimation { duration: 150 } }", source)

    def test_library_shows_filtered_game_count(self):
        source = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn('text: gameGrid.count + (gameGrid.count > 1 ? " JEUX" : " JEU")', source)


if __name__ == "__main__":
    unittest.main()
