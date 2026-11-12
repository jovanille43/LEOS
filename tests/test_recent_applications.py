"""Tests for safe recent-application history."""

import json
import os
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from desktop.recent_applications import RecentApplications, MAX_RECENT_ENTRIES


class RecentApplicationsTests(unittest.TestCase):
    def test_records_most_recent_first_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            history = RecentApplications(Path(directory) / "recent.json")
            history.record("org.example.Editor.desktop")
            history.record("org.example.Browser.desktop")
            history.record("org.example.Editor.desktop")
            self.assertEqual(
                history.items(),
                ["org.example.Editor.desktop", "org.example.Browser.desktop"],
            )

    def test_history_is_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            history = RecentApplications(Path(directory) / "recent.json", limit=3)
            for index in range(5):
                history.record(f"org.example.App{index}.desktop")
            self.assertEqual(
                history.items(),
                [
                    "org.example.App4.desktop",
                    "org.example.App3.desktop",
                    "org.example.App2.desktop",
                ],
            )

    def test_rejects_paths_commands_and_invalid_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            history = RecentApplications(Path(directory) / "recent.json")
            for value in ("../../app.desktop", "/usr/share/applications/app.desktop",
                          "app.desktop;rm", "command --option", ""):
                with self.subTest(value=value):
                    with self.assertRaises(ValueError):
                        history.record(value)

    def test_corrupt_history_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "recent.json"
            path.write_text("{broken", encoding="utf-8")
            history = RecentApplications(path)
            self.assertEqual(history.items(), [])
            with self.assertRaises(ValueError):
                history.record("org.example.App.desktop")
            self.assertEqual(path.read_text(encoding="utf-8"), "{broken")

    def test_oversized_history_is_rejected_without_overwriting(self):
        from desktop.recent_applications import MAX_RECENT_FILE_BYTES

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "recent.json"
            raw = b" " * (MAX_RECENT_FILE_BYTES + 1)
            path.write_bytes(raw)
            history = RecentApplications(path)
            self.assertEqual(history.items(), [])
            with self.assertRaisesRegex(ValueError, "unreadable"):
                history.record("org.example.Safe.desktop")
            self.assertEqual(path.read_bytes(), raw)

    def test_history_rejects_more_entries_than_the_global_limit(self):
        from desktop.recent_applications import MAX_RECENT_ENTRIES

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "recent.json"
            entries = [f"org.example.App{index}.desktop" for index in range(MAX_RECENT_ENTRIES + 1)]
            path.write_text(json.dumps(entries), encoding="utf-8")
            history = RecentApplications(path)
            self.assertEqual(history.items(), [])
            with self.assertRaises(ValueError):
                history.record("org.example.Safe.desktop")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), entries)

    def test_history_contains_only_desktop_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "recent.json"
            history = RecentApplications(path)
            history.record("org.example.Editor.desktop")
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload, ["org.example.Editor.desktop"])
            self.assertFalse(any("/" in item for item in payload))
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_reads_existing_order_and_ignores_symlink_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "recent.json"
            path.write_text(
                json.dumps(["org.example.First.desktop", "org.example.Second.desktop"]),
                encoding="utf-8",
            )
            history = RecentApplications(path)
            self.assertEqual(
                history.items(),
                ["org.example.First.desktop", "org.example.Second.desktop"],
            )
            if hasattr(Path, "symlink_to"):
                link = root / "linked.json"
                link.symlink_to(path)
                self.assertEqual(RecentApplications(link).items(), [])
                with self.assertRaises(ValueError):
                    RecentApplications(link).record("org.example.App.desktop")

    def test_empty_xdg_state_home_uses_standard_user_state_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            with patch.dict("os.environ", {"HOME": str(home), "XDG_STATE_HOME": ""}):
                history = RecentApplications()
            self.assertEqual(
                history.path,
                home / ".local" / "state" / "leos" / "recent-applications.json",
            )

    def test_clear_removes_history_atomically_and_keeps_private_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "recent.json"
            history = RecentApplications(path)
            history.record("org.example.Editor.desktop")
            history.clear()
            self.assertEqual(history.items(), [])
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), [])
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)


    def test_invalid_history_limits_are_rejected(self):
        for limit in (0, -1, MAX_RECENT_ENTRIES + 1, True, 1.5, "5"):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                RecentApplications(Path("recent.json"), limit=limit)

    def test_deeply_nested_json_is_ignored_without_crashing(self):
        from desktop.recent_applications import MAX_RECENT_FILE_BYTES

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "recent.json"
            path.write_text("[" * 2000 + "]" * 2000, encoding="utf-8")
            self.assertEqual(RecentApplications(path).items(), [])

    def test_history_reader_rejects_symlinked_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / "real"
            real.mkdir()
            (real / "recent.json").write_text("[]", encoding="utf-8")
            link = root / "linked"
            try:
                link.symlink_to(real, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Directory symbolic links unavailable")
            self.assertEqual(RecentApplications(link / "recent.json").items(), [])

    def test_writer_restricts_existing_directory_permissions(self):
        if os.name != "posix":
            self.skipTest("POSIX permissions unavailable")
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory) / "state"
            parent.mkdir(mode=0o755)
            parent.chmod(0o755)
            history = RecentApplications(parent / "recent.json")
            history.record("org.example.Editor.desktop")
            self.assertEqual(parent.stat().st_mode & 0o777, 0o700)
            self.assertEqual(history.path.stat().st_mode & 0o777, 0o600)

    def test_relative_xdg_state_home_falls_back_to_user_state_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            with patch.dict("os.environ", {"HOME": str(home), "XDG_STATE_HOME": "relative/state"}):
                history = RecentApplications()
            self.assertEqual(
                history.path,
                home / ".local" / "state" / "leos" / "recent-applications.json",
            )

if __name__ == "__main__":
    unittest.main()
