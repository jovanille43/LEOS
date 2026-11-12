"""Structural integration checks for RetroArch playlists in the unified library."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RetroArchLibraryIntegrationTests(unittest.TestCase):
    def test_library_discovers_local_playlists_and_thumbnail_roots(self):
        source = (ROOT / "gaming/backend/library.py").read_text(encoding="utf-8")
        self.assertIn("load_retroarch_games", source)
        self.assertIn("find_retroarch_playlist_directories", source)
        self.assertIn("find_retroarch_thumbnail_directories", source)
        self.assertIn("playlist_directories = self._retroarch_playlist_directories()", source)
        self.assertIn("thumbnail_directories=thumbnail_directories", source)

    def test_native_and_existing_flatpak_launchers_are_detected(self):
        source = (ROOT / "gaming/backend/library.py").read_text(encoding="utf-8")
        self.assertIn('native_retroarch = shutil.which("retroarch")', source)
        self.assertIn("self._flatpak_app_available(RETROARCH_FLATPAK_ID)", source)
        self.assertIn("native_executable=native_retroarch", source)
        self.assertIn("flatpak_available=flatpak_retroarch", source)

    def test_importer_stays_read_only_and_does_not_scan_or_download_roms(self):
        source = (ROOT / "gaming/backend/retroarch.py").read_text(encoding="utf-8")
        self.assertIn("MAX_PLAYLIST_BYTES", source)
        self.assertIn("MAX_PLAYLIST_ITEMS", source)
        self.assertIn("read_text(encoding=\"utf-8-sig\")", source)
        self.assertNotIn("requests.", source)
        self.assertNotIn("urlopen(", source)
        self.assertNotIn("os.walk(", source)


if __name__ == "__main__":
    unittest.main()
