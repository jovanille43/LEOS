"""Packaging and startup integration tests for the LEOS download organizer."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DownloadOrganizerIntegrationTests(unittest.TestCase):
    def test_kde_autostart_launches_per_user_organizer(self):
        entry = (ROOT / "desktop/autostart/leos-download-organizer.desktop").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "Exec=/usr/bin/python3 /usr/share/leos/gaming/download_organizer_service.py",
            entry,
        )
        self.assertIn("NoDisplay=true", entry)
        self.assertIn("X-KDE-autostart-phase=2", entry)

    def test_bluebuild_recipe_installs_download_organizer_autostart_entry(self):
        recipe = (ROOT / "recipes/common-modules.yml").read_text(encoding="utf-8")
        self.assertIn(
            "src: desktop/autostart/leos-download-organizer.desktop",
            recipe,
        )
        self.assertIn("dest: /usr/etc/xdg/autostart/", recipe)
        self.assertIn("src: gaming", recipe)
        self.assertIn("dest: /usr/share/leos/", recipe)

    def test_service_imports_from_installed_share_tree_and_uses_single_instance_lock(self):
        source = (ROOT / "gaming/download_organizer_service.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("PROJECT_ROOT = Path(__file__).resolve().parents[1]", source)
        self.assertIn("fcntl.LOCK_EX | fcntl.LOCK_NB", source)
        self.assertIn("organizer.poll()", source)
        self.assertIn("time.sleep(POLL_INTERVAL_SECONDS)", source)

    def test_download_organizer_does_not_auto_extract_or_execute_downloads(self):
        source = (ROOT / "gaming/backend/download_organizer.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("subprocess", source)
        self.assertIn("zipfile.ZipFile", source)
        self.assertIn("len(candidates) != 1", source)
        self.assertIn("path.rename(target)", source)
        self.assertIn('".wua": ("Nintendo", "Wii U")', source)


if __name__ == "__main__":
    unittest.main()
