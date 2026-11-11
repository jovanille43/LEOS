"""Tests for safe read-only cleanup previews."""
import tempfile
import unittest
from pathlib import Path

from control_center.cleanup import collect_cleanup_preview, _directory_summary


class CleanupPreviewTests(unittest.TestCase):
    def test_preview_counts_only_thumbnail_cache_and_trash_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            thumbnails = home / ".cache" / "thumbnails"
            trash = home / ".local" / "share" / "Trash" / "files"
            thumbnails.mkdir(parents=True)
            trash.mkdir(parents=True)
            (thumbnails / "thumb.png").write_bytes(b"12345")
            (trash / "deleted.txt").write_bytes(b"1234567")
            (home / ".cache" / "other-cache.bin").write_bytes(b"x" * 100)
            result = collect_cleanup_preview(home)
            self.assertEqual(result["thumbnails"]["files"], 1)
            self.assertEqual(result["thumbnails"]["bytes"], 5)
            self.assertEqual(result["trash"]["files"], 1)
            self.assertEqual(result["trash"]["bytes"], 7)
            self.assertEqual(result["totalBytes"], 12)
            self.assertTrue((thumbnails / "thumb.png").exists())
            self.assertTrue((trash / "deleted.txt").exists())

    def test_missing_directories_are_reported_as_unavailable(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = collect_cleanup_preview(Path(temporary))
            self.assertFalse(result["thumbnails"]["available"])
            self.assertFalse(result["trash"]["available"])
            self.assertEqual(result["totalBytes"], 0)

    def test_symlinks_are_not_followed_or_counted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            outside = root / "outside"
            outside.mkdir()
            (outside / "private.dat").write_bytes(b"private")
            target = root / "scan"
            target.mkdir()
            try:
                (target / "linked").symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("Symlinks are not available on this platform")
            result = _directory_summary(target)
            self.assertEqual(result["files"], 0)
            self.assertEqual(result["bytes"], 0)


if __name__ == "__main__":
    unittest.main()
