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

    def test_large_directory_scan_is_bounded_and_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index in range(12):
                (root / f"file-{index}.bin").write_bytes(b"x")
            result = _directory_summary(root, max_entries=5)
            self.assertTrue(result["truncated"])
            self.assertLessEqual(result["scannedEntries"], 5)
            self.assertLessEqual(result["files"], 5)

    def test_cleanup_preview_rejects_symlinked_parent_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "home"
            outside = Path(temporary) / "outside"
            home.mkdir()
            (outside / "thumbnails").mkdir(parents=True)
            (outside / "thumbnails" / "private.png").write_bytes(b"private")
            (outside / "Trash" / "files").mkdir(parents=True)
            (outside / "Trash" / "files" / "deleted.dat").write_bytes(b"private")

            try:
                (home / ".cache").symlink_to(outside, target_is_directory=True)
                local = home / ".local" / "share"
                local.mkdir(parents=True)
                (local / "Trash").symlink_to(outside / "Trash", target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Symbolic links are unavailable")

            result = collect_cleanup_preview(home)
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
