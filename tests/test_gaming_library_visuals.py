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

    def test_missing_or_broken_artwork_has_a_fallback(self):
        source = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("gameArtwork.status !== Image.Ready", source)
        self.assertIn("selectedGameArtwork.status !== Image.Ready", source)
        self.assertIn("window.selectedArtworkFailed", source)
        self.assertIn("onStatusChanged: window.selectedArtworkFailed = status === Image.Error", source)

    def test_refresh_clears_stale_selection(self):
        source = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("window.clearSelection()", source)
        self.assertIn("leos.refreshLibrary()", source)

    def test_empty_library_explains_supported_launchers_and_manual_refresh(self):
        source = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("Installe un jeu dans Steam, Heroic ou Lutris", source)
        self.assertIn("sélectionne ACTUALISER", source)
        self.assertIn("ajouter un jeu manuellement", source)
        self.assertNotIn("Steam sera analysé automatiquement", source)

    def test_empty_state_offers_contextual_actions(self):
        source = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("function activateEmptyStatePrimaryAction()", source)
        self.assertIn('id: emptyStatePrimaryButton', source)
        self.assertIn('searchField.clear()', source)
        self.assertIn('window.chooseCategory(0)', source)
        self.assertIn('leos.refreshLibrary()', source)
        self.assertIn('text: window.emptyStatePrimaryLabel()', source)

    def test_gamepad_confirm_activates_the_empty_state_primary_action(self):
        source = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn('emptyStatePrimaryButton.click()', source)
        self.assertIn('gameGrid.count === 0', source)

    def test_library_shows_filtered_game_count(self):
        source = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn('text: gameGrid.count + (gameGrid.count > 1 ? " JEUX" : " JEU")', source)


if __name__ == "__main__":
    unittest.main()
