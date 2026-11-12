"""Tests for verified Plasma configuration backup and restore."""
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from desktop.plasma_backup import PlasmaBackupManager


class PlasmaBackupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.config = root / "config" / "plasma-org.kde.plasma.desktop-appletsrc"
        self.backups = root / "state" / "plasma-backups"
        self.config.parent.mkdir(parents=True)
        self.config.write_text("[Containments]\nlayout=original\n", encoding="utf-8")
        self.manager = PlasmaBackupManager(self.config, self.backups)

    def tearDown(self):
        self.temporary.cleanup()

    def test_create_backup_and_verify_private_permissions(self):
        backup_id = self.manager.create_backup()
        self.assertEqual(self.manager.latest_backup_id(), backup_id)
        self.assertEqual((self.backups / f"{backup_id}.bak").read_text(encoding="utf-8"),
                         "[Containments]\nlayout=original\n")
        if os.name == "posix":
            self.assertEqual((self.backups / f"{backup_id}.bak").stat().st_mode & 0o777, 0o600)
            self.assertEqual(self.backups.stat().st_mode & 0o777, 0o700)

    def test_restore_requires_explicit_confirmation(self):
        backup_id = self.manager.create_backup()
        with self.assertRaises(PermissionError):
            self.manager.restore_backup(backup_id)

    def test_restore_preserves_current_config_before_replacing_it(self):
        backup_id = self.manager.create_backup()
        self.config.write_text("[Containments]\nlayout=changed\n", encoding="utf-8")
        previous_id = self.manager.restore_backup(backup_id, confirmed=True)
        self.assertEqual(self.config.read_text(encoding="utf-8"), "[Containments]\nlayout=original\n")
        self.assertIsNotNone(previous_id)
        self.assertEqual((self.backups / f"{previous_id}.bak").read_text(encoding="utf-8"),
                         "[Containments]\nlayout=changed\n")

    def test_tampered_backup_is_rejected(self):
        backup_id = self.manager.create_backup()
        (self.backups / f"{backup_id}.bak").write_text("tampered", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.manager.restore_backup(backup_id, confirmed=True)

    def test_invalid_backup_identifier_is_rejected(self):
        with self.assertRaises(ValueError):
            self.manager.restore_backup("../outside", confirmed=True)

    def test_backup_rejects_symlinked_config_directory(self):
        root = Path(self.temporary.name)
        actual = root / "actual-config"
        actual.mkdir()
        source = actual / "plasma-org.kde.plasma.desktop-appletsrc"
        source.write_text("[Containments]\\n", encoding="utf-8")
        linked = root / "linked-config"
        try:
            linked.symlink_to(actual, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolic links unavailable")
        manager = PlasmaBackupManager(
            linked / source.name, self.backups
        )
        with self.assertRaises(FileNotFoundError):
            manager.create_backup()

    def test_backup_rejects_symlinked_backup_parent(self):
        root = Path(self.temporary.name)
        actual = root / "actual-state"
        actual.mkdir()
        linked = root / "linked-state"
        try:
            linked.symlink_to(actual, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolic links unavailable")
        manager = PlasmaBackupManager(self.config, linked / "plasma-backups")
        with self.assertRaises(ValueError):
            manager.create_backup()

    def test_list_backups_scans_only_a_bounded_number_of_manifests(self):
        from desktop import plasma_backup

        backup_id = self.manager.create_backup()
        valid_manifest = self.backups / f"{backup_id}.json"
        original_glob = Path.glob

        def many_manifests(path, pattern):
            if path == self.backups and pattern == "*.json":
                return iter(
                    [self.backups / f"{index:032x}.json"
                     for index in range(plasma_backup.MAX_BACKUP_MANIFESTS_SCANNED)]
                    + [valid_manifest]
                )
            return original_glob(path, pattern)

        with patch("desktop.plasma_backup.Path.glob", new=many_manifests):
            self.assertEqual(self.manager.list_backups(), [])

    def test_missing_source_config_is_reported(self):
        self.config.unlink()
        with self.assertRaises(FileNotFoundError):
            self.manager.create_backup()

    def test_missing_config_is_created_when_restoring(self):
        backup_id = self.manager.create_backup()
        self.config.unlink()
        self.manager.restore_backup(backup_id, confirmed=True)
        self.assertEqual(self.config.read_text(encoding="utf-8"), "[Containments]\nlayout=original\n")

    def test_control_center_exposes_backup_without_automatic_restore(self):
        root = Path(__file__).resolve().parents[1]
        controller = (root / "control_center" / "controller.py").read_text(encoding="utf-8")
        qml = (root / "control_center" / "qml" / "Main.qml").read_text(encoding="utf-8")
        self.assertIn("PlasmaBackupManager()", controller)
        self.assertIn("def createPlasmaBackup(self)", controller)
        self.assertIn("controlCenter.createPlasmaBackup()", qml)
        self.assertNotIn("restorePlasmaBackup", qml)

    def test_oversized_manifest_is_not_listed_or_restored(self):
        from desktop.plasma_backup import MAX_BACKUP_MANIFEST_BYTES

        backup_id = self.manager.create_backup()
        manifest = self.backups / f"{backup_id}.json"
        with manifest.open("wb") as stream:
            stream.truncate(MAX_BACKUP_MANIFEST_BYTES + 1)
        self.assertIsNone(self.manager.latest_backup_id())
        with self.assertRaises(FileNotFoundError):
            self.manager.restore_backup(backup_id, confirmed=True)

    def test_corrupt_manifest_is_not_listed_or_restored(self):
        backup_id = self.manager.create_backup()
        (self.backups / f"{backup_id}.json").write_text("{broken", encoding="utf-8")
        self.assertIsNone(self.manager.latest_backup_id())
        with self.assertRaises(FileNotFoundError):
            self.manager.restore_backup(backup_id, confirmed=True)


if __name__ == "__main__":
    unittest.main()
