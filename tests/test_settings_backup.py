"""Tests for verified, private LEOS preference backups."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from leos_core.settings import DEFAULTS, SettingsStore
from leos_core.settings_backup import (
    MAX_BACKUP_MANIFESTS_SCANNED,
    SettingsBackupManager,
)


class SettingsBackupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.settings_path = root / "config" / "leos" / "settings.json"
        self.backup_dir = root / "state" / "leos" / "settings-backups"
        self.settings = SettingsStore(self.settings_path)
        self.manager = SettingsBackupManager(self.settings, self.backup_dir)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_create_backup_is_private_and_contains_complete_settings(self) -> None:
        self.settings.set_many({
            "theme_color_a": "#112233",
            "theme_color_b": "#AABBCC",
            "sounds_enabled": False,
        })
        backup_id = self.manager.create_backup()
        self.assertEqual(self.manager.latest_backup_id(), backup_id)
        payload = json.loads((self.backup_dir / f"{backup_id}.bak").read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(set(payload["settings"]), set(DEFAULTS))
        self.assertEqual(payload["settings"]["theme_color_a"], "#112233")
        self.assertFalse(payload["settings"]["sounds_enabled"])
        if os.name == "posix":
            self.assertEqual(self.backup_dir.stat().st_mode & 0o777, 0o700)
            self.assertEqual((self.backup_dir / f"{backup_id}.bak").stat().st_mode & 0o777, 0o600)
            self.assertEqual((self.backup_dir / f"{backup_id}.json").stat().st_mode & 0o777, 0o600)

    def test_restore_requires_explicit_confirmation(self) -> None:
        backup_id = self.manager.create_backup()
        with self.assertRaises(PermissionError):
            self.manager.restore_backup(backup_id)

    def test_restore_preserves_current_settings_before_replacing_them(self) -> None:
        self.settings.set_many({
            "theme_color_a": "#112233",
            "theme_color_b": "#AABBCC",
            "sounds_enabled": False,
        })
        backup_id = self.manager.create_backup()
        self.settings.set_many({
            "theme_color_a": "#445566",
            "theme_color_b": "#778899",
            "sounds_enabled": True,
        })

        recovery_id = self.manager.restore_backup(backup_id, confirmed=True)
        restored = SettingsStore(self.settings_path)
        self.assertEqual(restored.get("theme_color_a"), "#112233")
        self.assertEqual(restored.get("theme_color_b"), "#AABBCC")
        self.assertFalse(restored.get("sounds_enabled"))
        self.assertIsNotNone(self.manager._verified_backup(recovery_id))
        recovery = json.loads((self.backup_dir / f"{recovery_id}.bak").read_text(encoding="utf-8"))
        self.assertEqual(recovery["settings"]["theme_color_a"], "#445566")
        self.assertTrue(recovery["settings"]["sounds_enabled"])

    def test_verified_backup_can_recover_a_corrupt_settings_file(self) -> None:
        self.settings.set("theme_color_a", "#123456")
        backup_id = self.manager.create_backup()
        self.settings_path.write_text("{broken json", encoding="utf-8")
        self.manager.restore_backup(backup_id, confirmed=True)
        restored = SettingsStore(self.settings_path)
        self.assertEqual(restored.get("theme_color_a"), "#123456")
        self.assertNotEqual(self.settings_path.read_text(encoding="utf-8"), "{broken json")

    def test_tampered_backup_is_rejected(self) -> None:
        backup_id = self.manager.create_backup()
        (self.backup_dir / f"{backup_id}.bak").write_text("tampered", encoding="utf-8")
        self.assertEqual(self.manager.latest_backup_id(), None)
        with self.assertRaises(ValueError):
            self.manager.restore_backup(backup_id, confirmed=True)

    def test_invalid_backup_identifier_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.manager.restore_backup("../outside", confirmed=True)

    def test_backup_rejects_symlinked_backup_directory(self) -> None:
        root = Path(self.temporary.name)
        actual = root / "actual"
        actual.mkdir()
        linked = root / "linked"
        try:
            linked.symlink_to(actual, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolic links unavailable")
        manager = SettingsBackupManager(self.settings, linked / "settings-backups")
        with self.assertRaises(ValueError):
            manager.create_backup()

    def test_symlinked_backup_file_is_not_listed_or_restored(self) -> None:
        backup_id = self.manager.create_backup()
        backup = self.backup_dir / f"{backup_id}.bak"
        external = self.backup_dir / "external.bak"
        external.write_bytes(backup.read_bytes())
        backup.unlink()
        try:
            backup.symlink_to(external)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolic links unavailable")
        self.assertEqual(self.manager.latest_backup_id(), None)
        with self.assertRaises(ValueError):
            self.manager.restore_backup(backup_id, confirmed=True)

    def test_manifest_with_wrong_digest_is_ignored(self) -> None:
        backup_id = self.manager.create_backup()
        manifest_path = self.backup_dir / f"{backup_id}.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["sha256"] = "0" * 64
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertEqual(self.manager.list_backups(), [])

    def test_backup_validation_rejects_incomplete_or_invalid_settings(self) -> None:
        backup_id = self.manager.create_backup()
        backup_path = self.backup_dir / f"{backup_id}.bak"
        payload = json.loads(backup_path.read_text(encoding="utf-8"))
        payload["settings"].pop("theme_color_a")
        data = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
        backup_path.write_bytes(data)
        manifest_path = self.backup_dir / f"{backup_id}.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        import hashlib
        manifest["size"] = len(data)
        manifest["sha256"] = hashlib.sha256(data).hexdigest()
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertEqual(self.manager.list_backups(), [])
        with self.assertRaises(ValueError):
            self.manager.restore_backup(backup_id, confirmed=True)

    def test_older_verified_backup_can_be_restored_without_losing_current_state(self) -> None:
        self.settings.set("theme_color_a", "#112233")
        older_backup = self.manager.create_backup()
        self.settings.set("theme_color_a", "#445566")
        newer_backup = self.manager.create_backup()

        recovery_backup = self.manager.restore_backup(older_backup, confirmed=True)

        self.assertEqual(SettingsStore(self.settings_path).get("theme_color_a"), "#112233")
        self.assertNotEqual(older_backup, newer_backup)
        recovery = self.manager._verified_backup(recovery_backup)
        self.assertIsNotNone(recovery)
        self.assertEqual(recovery[1]["theme_color_a"], "#445566")
        self.assertIsNotNone(self.manager._verified_backup(newer_backup))

    def test_backup_retention_keeps_only_the_most_recent_verified_copies(self) -> None:
        from leos_core.settings_backup import MAX_RETAINED_BACKUPS

        created = [
            self.manager.create_backup()
            for _ in range(MAX_RETAINED_BACKUPS + 3)
        ]
        entries = self.manager.list_backups()
        self.assertEqual(len(entries), MAX_RETAINED_BACKUPS)
        self.assertEqual(self.manager.latest_backup_id(), created[-1])
        self.assertNotIn(created[0], [entry["backup_id"] for entry in entries])

    def test_backup_scan_is_bounded(self) -> None:
        from unittest.mock import patch

        backup_id = self.manager.create_backup()
        valid_path = self.backup_dir / f"{backup_id}.json"
        original_glob = Path.glob

        def bounded_glob(path: Path, pattern: str):
            if path == self.backup_dir and pattern == "*.json":
                return iter(
                    [self.backup_dir / f"{index:032x}.json"
                     for index in range(MAX_BACKUP_MANIFESTS_SCANNED)]
                    + [valid_path]
                )
            return original_glob(path, pattern)

        with patch("leos_core.settings_backup.Path.glob", new=bounded_glob):
            self.assertEqual(self.manager.list_backups(), [])


if __name__ == "__main__":
    unittest.main()
