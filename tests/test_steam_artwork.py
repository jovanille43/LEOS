"""Tests for reading local Steam artwork cache layouts."""

import tempfile
import unittest
from pathlib import Path

from gaming.backend.steam_artwork import find_steam_artwork


class SteamArtworkTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def make_art(self, relative_path: str) -> Path:
        path = self.cache / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"test-image")
        return path

    def test_prefers_high_resolution_portrait_in_flat_app_directory(self):
        low = self.make_art("123/library_600x900.jpg")
        high = self.make_art("123/library_600x900_2x.jpg")
        self.assertEqual(find_steam_artwork(self.cache, "123"), high)
        self.assertTrue(low.is_file())

    def test_finds_portrait_in_content_hash_subdirectory(self):
        art = self.make_art("123/abc123/library_600x900.jpg")
        self.assertEqual(find_steam_artwork(self.cache, "123"), art)

    def test_supports_legacy_flat_cache_layout(self):
        art = self.make_art("123_library_600x900.jpg")
        self.assertEqual(find_steam_artwork(self.cache, "123"), art)

    def test_uses_header_when_portrait_is_unavailable(self):
        art = self.make_art("123/abc123/library_header.jpg")
        self.assertEqual(find_steam_artwork(self.cache, "123"), art)

    def test_rejects_invalid_app_id_and_missing_artwork(self):
        self.assertIsNone(find_steam_artwork(self.cache, "../123"))
        self.assertIsNone(find_steam_artwork(self.cache, "123"))


if __name__ == "__main__":
    unittest.main()
