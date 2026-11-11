"""Tests for safe recent-application history."""

import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from desktop.recent_applications import RecentApplications


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


if __name__ == "__main__":
    unittest.main()
