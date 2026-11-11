"""Tests for pure LEOS game-library category filtering."""

import unittest

from gaming.backend.library_state import filter_games


class LibraryStateTests(unittest.TestCase):
    def setUp(self):
        self.games = [
            {"id": "steam:1", "title": "Alpha", "platform": "PC"},
            {"id": "manual:zelda", "title": "Zelda", "platform": "Nintendo"},
            {"id": "manual:ps", "title": "Racer", "platform": "PlayStation"},
            {"id": "manual:arcade", "title": "Arcade", "platform": "Arcade"},
            {"id": "manual:sega", "title": "Sonic", "platform": "SEGA"},
        ]

    def test_home_returns_all_games(self):
        self.assertEqual(len(filter_games(self.games, "Accueil", set(), [])), 5)

    def test_platform_categories_filter_correctly(self):
        self.assertEqual(
            [item["id"] for item in filter_games(self.games, "Nintendo", set(), [])],
            ["manual:zelda"],
        )
        self.assertEqual(
            [item["id"] for item in filter_games(self.games, "PC Gaming", set(), [])],
            ["steam:1"],
        )

    def test_favorites_filter_by_game_identifier(self):
        result = filter_games(self.games, "Favoris", {"steam:1", "manual:sega"}, [])
        self.assertEqual([item["id"] for item in result], ["steam:1", "manual:sega"])

    def test_recent_games_follow_most_recent_order(self):
        result = filter_games(
            self.games, "Récemment joués", set(), ["manual:sega", "steam:1"]
        )
        self.assertEqual([item["id"] for item in result], ["manual:sega", "steam:1"])

    def test_search_matches_title_platform_and_source_case_insensitively(self):
        self.assertEqual(
            [game["id"] for game in filter_games(
                self.games, "Accueil", set(), [], "SONIC"
            )],
            ["manual:sega"],
        )
        self.assertEqual(
            [game["id"] for game in filter_games(
                self.games, "PC Gaming", set(), [], "pc"
            )],
            ["steam:1"],
        )
        self.assertEqual(
            [game["id"] for game in filter_games(
                self.games, "Accueil", set(), [], "playstation"
            )],
            ["manual:ps"],
        )

    def test_search_is_applied_after_category_filtering(self):
        result = filter_games(
            self.games, "Nintendo", set(), [], "racer"
        )
        self.assertEqual(result, [])

    def test_unknown_category_falls_back_to_all_games(self):
        self.assertEqual(len(filter_games(self.games, "Unknown", set(), [])), 5)


if __name__ == "__main__":
    unittest.main()
