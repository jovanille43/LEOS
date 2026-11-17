"""Regression tests for persisted gaming-library references."""

import unittest
from pathlib import Path

from gaming.backend.library_state import (
    filter_games,
    retain_saved_library_references,
)


class SavedLibraryReferenceTests(unittest.TestCase):
    def test_offline_favourites_and_recent_games_are_retained(self):
        favorites, recent = retain_saved_library_references(
            ["steam:offline", "steam:installed"],
            ["steam:offline", "steam:installed"],
        )

        self.assertEqual(favorites, {"steam:offline", "steam:installed"})
        self.assertEqual(recent, ["steam:offline", "steam:installed"])

    def test_unavailable_games_remain_hidden_without_being_forgotten(self):
        favorites, recent = retain_saved_library_references(
            ["steam:offline", "steam:installed"],
            ["steam:offline", "steam:installed"],
        )
        visible_games = [
            {"id": "steam:installed", "title": "Installed Game", "platform": "PC"},
        ]

        self.assertEqual(
            [game["id"] for game in filter_games(
                visible_games, "Favoris", favorites, recent
            )],
            ["steam:installed"],
        )
        self.assertEqual(
            [game["id"] for game in filter_games(
                visible_games, "Récemment joués", favorites, recent
            )],
            ["steam:installed"],
        )
        self.assertIn("steam:offline", favorites)
        self.assertIn("steam:offline", recent)

    def test_saved_references_are_deduplicated_and_bounded(self):
        favorite_values = [
            "steam:one", "steam:one", " steam:two ", "", "bad" + chr(0) + "id"
        ]
        recent_values = [f"steam:{index}" for index in range(60)]
        favorites, recent = retain_saved_library_references(
            favorite_values, recent_values
        )

        self.assertEqual(favorites, {"steam:one", "steam:two"})
        self.assertEqual(len(recent), 50)
        self.assertEqual(recent[0], "steam:0")
        self.assertEqual(recent[-1], "steam:49")

    def test_library_scanner_cannot_restart_or_update_after_shutdown(self):
        root = Path(__file__).resolve().parents[1]
        library = (root / "gaming/backend/library.py").read_text(encoding="utf-8")
        controller = (root / "gaming/backend/controller.py").read_text(encoding="utf-8")

        refresh = library[
            library.index("def refresh(self)"):
            library.index("def _on_library_scan_completed")
        ]
        completed = library[
            library.index("def _on_library_scan_completed"):
            library.index("def _collect_library_snapshot")
        ]
        shutdown = library[
            library.index("def shutdown(self)"):
            library.index("def roleNames")
        ]
        gaming_shutdown = controller[
            controller.index("def shutdown(self)"):
            controller.index("@Slot()", controller.index("def shutdown(self)"))
        ]

        self.assertIn("if self._closed:", refresh)
        self.assertIn("if self._closed:", completed)
        self.assertIn("self._closed = True", shutdown)
        self.assertIn("self._refresh_pending = False", shutdown)
        self.assertIn("self.library.shutdown()", gaming_shutdown)

    def test_non_list_persistence_is_treated_as_empty(self):
        self.assertEqual(
            retain_saved_library_references({"steam:one"}, None),
            (set(), []),
        )


if __name__ == "__main__":
    unittest.main()
