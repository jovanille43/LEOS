"""Tests for the LEOS Gaming per-user single-instance lock."""

import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_symlink_lock_directory_is_rejected(self):
        import os

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real = root / "real"
            real.mkdir()
            linked = root / "linked"
            try:
                os.symlink(real, linked, target_is_directory=True)
            except (NotImplementedError, OSError):
                self.skipTest("Symlinks unavailable in this environment")
            with self.assertRaises(OSError):
                acquire_instance_lock("gaming", linked)
            self.assertEqual(list(real.iterdir()), [])

    def test_overlong_lock_identifier_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "too long"):
                acquire_instance_lock("g" * 65, Path(temporary))

    def test_lock_directory_permissions_are_private(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "leos"
            lock = acquire_instance_lock("gaming", directory)
            self.assertIsNotNone(lock)
            self.assertEqual(directory.stat().st_mode & 0o777, 0o700)
            lock.release()

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

    def test_lock_directory_is_restricted_to_the_current_user(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "leos"
            directory.mkdir(mode=0o755)
            directory.chmod(0o755)
            lock = acquire_instance_lock("gaming", directory)
            self.assertIsNotNone(lock)
            try:
                self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)
            finally:
                lock.release()

    def test_lock_directory_rejects_a_different_owner(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "leos"
            directory.mkdir(mode=0o700)
            current_uid = os.getuid()
            with patch("gaming.backend.instance_lock.os.getuid", return_value=current_uid + 1):
                with self.assertRaisesRegex(OSError, "current user"):
                    acquire_instance_lock("gaming", directory)

    def test_lock_file_rejects_hardlinks_without_changing_the_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / "leos"
            directory.mkdir(mode=0o700)
            directory.chmod(0o700)
            target = root / "target"
            target.write_text("keep unchanged", encoding="utf-8")
            target.chmod(0o640)
            (directory / "gaming.lock").hardlink_to(target)

            with self.assertRaisesRegex(OSError, "owned, private regular file"):
                acquire_instance_lock("gaming", directory)

            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o640)
            self.assertEqual(target.read_text(encoding="utf-8"), "keep unchanged")

    def test_lock_file_rejects_a_different_owner_before_chmod(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "leos"
            directory.mkdir(mode=0o700)
            directory.chmod(0o700)
            lock_path = directory / "gaming.lock"
            lock_path.write_text("existing lock", encoding="utf-8")
            lock_path.chmod(0o640)
            current_uid = os.getuid()
            with patch(
                "gaming.backend.instance_lock.os.getuid",
                side_effect=[current_uid, current_uid + 1],
            ):
                with self.assertRaisesRegex(OSError, "owned, private regular file"):
                    acquire_instance_lock("gaming", directory)
            self.assertEqual(stat.S_IMODE(lock_path.stat().st_mode), 0o640)

    def test_relative_xdg_runtime_directory_falls_back_to_absolute_cache_home(self):
        with tempfile.TemporaryDirectory() as temporary:
            cache_home = Path(temporary) / "cache"
            with patch.dict(
                os.environ,
                {
                    "XDG_RUNTIME_DIR": "relative/runtime",
                    "XDG_CACHE_HOME": str(cache_home),
                },
            ):
                lock = acquire_instance_lock("gaming")
                self.assertIsNotNone(lock)
                try:
                    self.assertTrue((cache_home / "leos" / "gaming.lock").is_file())
                finally:
                    lock.release()

    def test_explicit_relative_lock_directory_is_rejected(self):
        with self.assertRaisesRegex(OSError, "absolute path"):
            acquire_instance_lock("gaming", Path("relative/leos"))

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
