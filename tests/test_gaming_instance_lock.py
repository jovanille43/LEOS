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
                first.unlock()

            third = acquire_instance_lock("gaming", directory)
            self.assertIsNotNone(third)
            third.unlock()

    def test_lock_identifier_cannot_escape_lock_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            lock = acquire_instance_lock("../../gaming", directory)
            self.assertIsNotNone(lock)
            self.assertEqual(
                sorted(path.name for path in directory.iterdir()),
                ["gaming.lock"],
            )
            lock.unlock()

    def test_empty_lock_identifier_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                acquire_instance_lock("../...", Path(temporary))


if __name__ == "__main__":
    unittest.main()
