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
        self.assertIn("Behavior on border.color { ColorAnimation { duration: 160; easing.type: Easing.OutCubic } }", source)

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

    def test_empty_state_uses_official_gaming_emblem_and_editorial_layout(self):
        source = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("id: emptyStateSurface", source)
        self.assertIn("id: emptyStateEmblem", source)
        self.assertIn("source: leosTheme.gamingLogoUrl", source)
        self.assertIn("function emptyStateTitle()", source)
        self.assertIn("function emptyStateDescription()", source)
        self.assertIn("text: window.emptyStateTitle()", source)
        self.assertIn("Layout.maximumWidth: 410", source)

    def test_library_shows_filtered_game_count(self):
        source = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn('text: gameGrid.count + (gameGrid.count > 1 ? " JEUX" : " JEU")', source)

    def test_game_cards_distinguish_selected_hovered_and_keyboard_focused_states(self):
        qml = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("window.selectedIndex === gameCard.index || gameCard.hovered", qml)
        self.assertIn("gameCard.activeFocus ? 2 : 1", qml)
        self.assertIn("gameCard.hovered ? window.accentB", qml)
        self.assertIn("visible: window.selectedIndex === gameCard.index || gameCard.hovered", qml)
        self.assertIn("GradientStop { position: 0; color: window.accentA }", qml)
        self.assertIn("GradientStop { position: 1; color: window.accentB }", qml)

    def test_library_category_rail_and_game_details_adapt_to_compact_widths(self):
        qml = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("Layout.preferredWidth: window.width < 1180 ? 150 : 190", qml)
        self.assertIn("Layout.preferredWidth: window.width < 1180 ? 230 : 280", qml)
        self.assertIn("Layout.minimumWidth: 140", qml)
        self.assertIn("Layout.minimumWidth: 210", qml)

    def test_category_buttons_keep_selection_when_hovering_other_categories(self):
        qml = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("modelData === window.selectedCategory || categoryButton.hovered", qml)
        self.assertIn("visible: modelData === window.selectedCategory", qml)




    def test_game_cards_use_framed_cover_art_and_editorial_metadata_pills(self):
        qml = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("id: favoriteChipLabel", qml)
        self.assertIn('text: "FAVORI"', qml)
        self.assertIn("id: platformChipLabel", qml)
        self.assertIn("text: gameCard.source", qml)
        self.assertIn("anchors.margins: 1", qml)
        self.assertIn("opacity: window.selectedIndex === gameCard.index ? 1 : gameCard.hovered ? 0.72 : 0", qml)
        self.assertIn('text: "TA COLLECTION"', qml)
        self.assertIn("implicitWidth: 92", qml)

if __name__ == "__main__":
    unittest.main()
