"""Tests for the LEOS Gaming per-user single-instance lock."""

import tempfile
import unittest
from pathlib import Path

from gaming.backend.instance_lock import acquire_instance_lock


class GamingInstanceLockTests(unittest.TestCase):
    def test_second_instance_is_rejected_until_first_releases_lock(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            first = acquire_instance_lock("gaming", directory)
            self.assertIsNotNone(first)
            try:
                self.assertIsNone(acquire_instance_lock("gaming", directory))
            finally:
                first.release()

            third = acquire_instance_lock("gaming", directory)
            self.assertIsNotNone(third)
            third.release()

    def test_lock_identifier_cannot_escape_lock_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            lock = acquire_instance_lock("../../gaming", directory)
            self.assertIsNotNone(lock)
            self.assertEqual(
                sorted(path.name for path in directory.iterdir()),
                ["gaming.lock"],
            )
            lock.release()

    def test_empty_lock_identifier_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                acquire_instance_lock("../...", Path(temporary))

    def test_lock_file_is_private_and_release_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "leos"
            lock = acquire_instance_lock("gaming", directory)
            self.assertIsNotNone(lock)
            lock_path = directory / "gaming.lock"
            self.assertEqual(lock_path.stat().st_mode & 0o777, 0o600)
            lock.release()
            lock.release()

            replacement = acquire_instance_lock("gaming", directory)
            self.assertIsNotNone(replacement)
            replacement.release()

    def test_different_application_ids_have_independent_locks(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            gaming = acquire_instance_lock("gaming", directory)
            selector = acquire_instance_lock("selector", directory)
            self.assertIsNotNone(gaming)
            self.assertIsNotNone(selector)
            gaming.release()
            selector.release()

    def test_symlink_lock_file_is_rejected(self):
        import os

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            target = directory / "target"
            target.write_text("do not follow", encoding="utf-8")
            link = directory / "gaming.lock"
            try:
                os.symlink(target, link)
            except (NotImplementedError, OSError):
                self.skipTest("Symlinks unavailable in this environment")
            with self.assertRaises(OSError):
                acquire_instance_lock("gaming", directory)
            self.assertEqual(target.read_text(encoding="utf-8"), "do not follow")

    def test_kernel_releases_lock_after_owner_exits_abnormally(self):
        import subprocess
        import sys

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            script = (
                "import os, sys\n"
                "from pathlib import Path\n"
                "from gaming.backend.instance_lock import acquire_instance_lock\n"
                "lock = acquire_instance_lock('gaming', Path(sys.argv[1]))\n"
                "if lock is None: os._exit(2)\n"
                "sys.stdout.write('LOCKED\\n'); sys.stdout.flush()\n"
                "os._exit(23)\n"
            )
            result = subprocess.run(
                [sys.executable, "-c", script, str(directory)],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            self.assertEqual(result.returncode, 23)
            self.assertEqual(result.stdout.strip(), "LOCKED")

            replacement = acquire_instance_lock("gaming", directory)
            self.assertIsNotNone(replacement)
            replacement.release()


if __name__ == "__main__":
    unittest.main()
