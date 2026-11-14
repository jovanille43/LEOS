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

    def test_restore_preserves_selected_old_backup_when_retention_is_full(self) -> None:
        from leos_core.settings_backup import MAX_RETAINED_BACKUPS

        backup_ids = []
        for index in range(MAX_RETAINED_BACKUPS):
            self.settings.set("theme_color_a", f"#{index + 1:06X}")
            backup_ids.append(self.manager.create_backup())
        selected_backup = backup_ids[0]
        newest_colour = f"#{MAX_RETAINED_BACKUPS:06X}"

        recovery_backup = self.manager.restore_backup(selected_backup, confirmed=True)

        self.assertEqual(SettingsStore(self.settings_path).get("theme_color_a"), "#000001")
        self.assertIsNotNone(self.manager._verified_backup(selected_backup))
        recovery = self.manager._verified_backup(recovery_backup)
        self.assertIsNotNone(recovery)
        self.assertEqual(recovery[1]["theme_color_a"], newest_colour)
        self.assertEqual(len(self.manager.list_backups()), MAX_RETAINED_BACKUPS)

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

    def test_export_copies_verified_backup_pair_to_external_directory(self) -> None:
        import hashlib

        backup_id = self.manager.create_backup()
        export_dir = Path(self.temporary.name) / "external-drive"
        export_dir.mkdir()
        backup_source = self.backup_dir / f"{backup_id}.bak"
        manifest_source = self.backup_dir / f"{backup_id}.json"

        exported_backup, exported_manifest = self.manager.export_backup(backup_id, export_dir)

        self.assertEqual(exported_backup, export_dir / f"{backup_id}.bak")
        self.assertEqual(exported_manifest, export_dir / f"{backup_id}.json")
        self.assertEqual(exported_backup.read_bytes(), backup_source.read_bytes())
        self.assertEqual(exported_manifest.read_bytes(), manifest_source.read_bytes())
        manifest = json.loads(exported_manifest.read_text(encoding="utf-8"))
        self.assertEqual(manifest["sha256"], hashlib.sha256(exported_backup.read_bytes()).hexdigest())
        if os.name == "posix":
            self.assertEqual(exported_backup.stat().st_mode & 0o777, 0o600)
            self.assertEqual(exported_manifest.stat().st_mode & 0o777, 0o600)

    def test_export_refuses_to_overwrite_an_existing_backup_pair(self) -> None:
        backup_id = self.manager.create_backup()
        export_dir = Path(self.temporary.name) / "external-drive"
        export_dir.mkdir()
        existing = export_dir / f"{backup_id}.json"
        existing.write_text("keep this file", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            self.manager.export_backup(backup_id, export_dir)
        self.assertEqual(existing.read_text(encoding="utf-8"), "keep this file")
        self.assertFalse((export_dir / f"{backup_id}.bak").exists())

    def test_export_rejects_relative_or_symlinked_destinations(self) -> None:
        backup_id = self.manager.create_backup()
        with self.assertRaises(ValueError):
            self.manager.export_backup(backup_id, Path("relative-folder"))
        root = Path(self.temporary.name)
        target = root / "external"
        target.mkdir()
        linked = root / "linked-external"
        try:
            linked.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolic links unavailable")
        with self.assertRaises(ValueError):
            self.manager.export_backup(backup_id, linked)

    def test_failed_second_export_file_removes_first_partial_file(self) -> None:
        from unittest.mock import patch

        backup_id = self.manager.create_backup()
        export_dir = Path(self.temporary.name) / "external-drive"
        export_dir.mkdir()
        original = self.manager._write_new_export_file
        calls = 0

        def fail_second(directory: Path, filename: str, data: bytes) -> Path:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("simulated removable-drive error")
            return original(directory, filename, data)

        with patch.object(self.manager, "_write_new_export_file", side_effect=fail_second):
            with self.assertRaises(OSError):
                self.manager.export_backup(backup_id, export_dir)
        self.assertEqual(list(export_dir.iterdir()), [])

    def test_external_backup_pair_can_be_imported_and_restored(self) -> None:
        self.settings.set_many({
            "theme_color_a": "#123456",
            "theme_color_b": "#ABCDEF",
            "sounds_enabled": False,
        })
        backup_id = self.manager.create_backup()
        export_dir = Path(self.temporary.name) / "external-drive"
        export_dir.mkdir()
        self.manager.export_backup(backup_id, export_dir)

        imported_config = Path(self.temporary.name) / "imported-config" / "settings.json"
        imported_settings = SettingsStore(imported_config)
        imported_manager = SettingsBackupManager(
            imported_settings,
            Path(self.temporary.name) / "imported-state" / "settings-backups",
        )
        imported_id = imported_manager.import_backup(export_dir / f"{backup_id}.json")

        self.assertEqual(imported_id, backup_id)
        self.assertEqual(imported_manager.latest_backup_id(), backup_id)
        imported_manager.restore_backup(imported_id, confirmed=True)
        restored = SettingsStore(imported_config)
        self.assertEqual(restored.get("theme_color_a"), "#123456")
        self.assertEqual(restored.get("theme_color_b"), "#ABCDEF")
        self.assertFalse(restored.get("sounds_enabled"))

    def test_import_rejects_a_tampered_external_pair_without_copying_files(self) -> None:
        import hashlib

        backup_id = self.manager.create_backup()
        export_dir = Path(self.temporary.name) / "external-drive"
        export_dir.mkdir()
        self.manager.export_backup(backup_id, export_dir)
        backup_path = export_dir / f"{backup_id}.bak"
        backup_path.write_bytes(backup_path.read_bytes() + b"tamper")

        imported_manager = SettingsBackupManager(
            SettingsStore(Path(self.temporary.name) / "imported.json"),
            Path(self.temporary.name) / "imported-backups",
        )
        with self.assertRaises(ValueError):
            imported_manager.import_backup(export_dir / f"{backup_id}.json")
        self.assertFalse((imported_manager.backup_dir / f"{backup_id}.bak").exists())
        self.assertFalse((imported_manager.backup_dir / f"{backup_id}.json").exists())

    def test_import_refuses_to_overwrite_an_existing_local_backup(self) -> None:
        backup_id = self.manager.create_backup()
        export_dir = Path(self.temporary.name) / "external-drive"
        export_dir.mkdir()
        self.manager.export_backup(backup_id, export_dir)
        original = (self.backup_dir / f"{backup_id}.bak").read_bytes()
        with self.assertRaises(FileExistsError):
            self.manager.import_backup(export_dir / f"{backup_id}.json")
        self.assertEqual((self.backup_dir / f"{backup_id}.bak").read_bytes(), original)

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
