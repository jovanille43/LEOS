"""Tests for conservative game-title normalization and duplicate hints."""

import unittest

from gaming.backend.library_state import (
    duplicate_title_metadata,
    filter_games,
    normalize_display_title,
    normalize_search_text,
    title_identity_key,
)


class GameTitleMetadataTests(unittest.TestCase):
    def test_display_title_only_collapses_whitespace(self):
        self.assertEqual(normalize_display_title("  FINAL   Fantasy  VII  "), "FINAL Fantasy VII")

    def test_identity_key_is_case_and_unicode_normalized(self):
        self.assertEqual(title_identity_key("  CAFÉ  "), title_identity_key("cafe\u0301"))

    def test_edition_markers_remain_distinct(self):
        self.assertNotEqual(
            title_identity_key("Example Game"),
            title_identity_key("Example Game: Deluxe Edition"),
        )

    def test_duplicate_hint_does_not_merge_provider_records(self):
        games = [
            {"id": "steam:1", "title": "Same Game", "source": "Steam"},
            {"id": "heroic:gog:same", "title": " same   game ", "source": "GOG · Heroic"},
            {"id": "steam:2", "title": "Same Game: GOTY", "source": "Steam"},
        ]
        metadata = duplicate_title_metadata(games)
        self.assertEqual(metadata["steam:1"]["count"], 2)
        self.assertEqual(metadata["heroic:gog:same"]["count"], 2)
        self.assertNotIn("steam:2", metadata)
        self.assertEqual(len(games), 3)

    def test_search_ignores_accents_and_repeated_whitespace(self):
        games = [{"id": "steam:1", "title": "Café   Racer", "platform": "PC", "source": "Steam"}]
        self.assertEqual(normalize_search_text("  cafe   racer "), "cafe racer")
        self.assertEqual(
            [game["id"] for game in filter_games(games, "Accueil", set(), [], "CAFE RACER")],
            ["steam:1"],
        )


if __name__ == "__main__":
    unittest.main()
