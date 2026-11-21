"""Cross-process synchronization for all LEOS Flatpak transactions."""

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from leos_core.flatpak_lock import release_flatpak_lock, try_acquire_flatpak_lock


class FlatpakLockTests(unittest.TestCase):
    def test_lock_interoperates_with_the_shell_flock_used_by_first_run(self):
        with tempfile.TemporaryDirectory() as directory:
            state_home = Path(directory) / "state"
            with patch.dict(os.environ, {"XDG_STATE_HOME": str(state_home)}):
                descriptor = try_acquire_flatpak_lock()
                self.assertIsNotNone(descriptor)
                lock_path = state_home / "leos" / "flatpak-setup.lock"
                self.assertTrue(lock_path.is_file())
                self.assertEqual(stat.S_IMODE(lock_path.stat().st_mode), 0o600)

                blocked = subprocess.run(
                    ["/usr/bin/flock", "-n", str(lock_path), "/usr/bin/true"],
                    capture_output=True,
                    check=False,
                )
                self.assertNotEqual(blocked.returncode, 0)

                release_flatpak_lock(descriptor)
                available = subprocess.run(
                    ["/usr/bin/flock", "-n", str(lock_path), "/usr/bin/true"],
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(available.returncode, 0)

    def test_a_second_python_client_fails_fast_while_the_lock_is_held(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"XDG_STATE_HOME": str(Path(directory) / "state")}):
                descriptor = try_acquire_flatpak_lock()
                self.assertIsNotNone(descriptor)
                try:
                    self.assertIsNone(try_acquire_flatpak_lock())
                finally:
                    release_flatpak_lock(descriptor)

    def test_lock_can_be_reacquired_after_release(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"XDG_STATE_HOME": str(Path(directory) / "state")}):
                first = try_acquire_flatpak_lock()
                self.assertIsNotNone(first)
                release_flatpak_lock(first)
                second = try_acquire_flatpak_lock()
                self.assertIsNotNone(second)
                release_flatpak_lock(second)

    def test_symlinked_state_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_home = root / "state"
            target = root / "target"
            target.mkdir()
            state_home.mkdir()
            (state_home / "leos").symlink_to(target, target_is_directory=True)
            with patch.dict(os.environ, {"XDG_STATE_HOME": str(state_home)}):
                with self.assertRaises(OSError):
                    try_acquire_flatpak_lock()

    def test_symlinked_lock_file_is_rejected_without_touching_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_home = root / "state"
            state_dir = state_home / "leos"
            state_dir.mkdir(parents=True)
            target = root / "target"
            target.write_text("keep", encoding="utf-8")
            (state_dir / "flatpak-setup.lock").symlink_to(target)
            with patch.dict(os.environ, {"XDG_STATE_HOME": str(state_home)}):
                with self.assertRaises(OSError):
                    try_acquire_flatpak_lock()
            self.assertEqual(target.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
