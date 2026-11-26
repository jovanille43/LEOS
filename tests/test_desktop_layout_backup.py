"""Tests for verified, private LEOS desktop layout backups."""
import tempfile
import unittest
from pathlib import Path

from desktop.layout_backup import (
    DesktopLayoutBackupManager,
    MAX_RETAINED_BACKUPS,
)
from desktop.layouts import DesktopLayoutStore, DEFAULT_LAYOUT


class DesktopLayoutBackupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.layout_path = self.root / "config" / "desktop-layout.json"
        self.backups = self.root / "state" / "desktop-layout-backups"
        self.store = DesktopLayoutStore(self.layout_path)
        self.manager = DesktopLayoutBackupManager(self.store, self.backups)

    def tearDown(self):
        self.temporary.cleanup()

    def test_backup_is_private_and_contains_a_verified_layout(self):
        self.store.apply_profile("workspace")
        backup_id = self.manager.create_backup()
        entries = self.manager.list_backups()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["backup_id"], backup_id)
        self.assertEqual((self.backups / f"{backup_id}.bak").stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.backups.stat().st_mode & 0o777, 0o700)

    def test_restore_requires_explicit_confirmation(self):
        self.store.apply_profile("minimal")
        backup_id = self.manager.create_backup()
        with self.assertRaises(PermissionError):
            self.manager.restore_backup(backup_id)

    def test_restore_preserves_the_current_layout_before_replacing_it(self):
        self.store.apply_profile("workspace")
        backup_id = self.manager.create_backup()
        self.store.apply_profile("minimal")
        recovery_id = self.manager.restore_backup(backup_id, confirmed=True)
        self.assertEqual(self.store.get()["profile"], "workspace")
        self.assertNotEqual(recovery_id, backup_id)
        self.assertEqual(len(self.manager.list_backups()), 2)
        recovery = next(item for item in self.manager.list_backups() if item["backup_id"] == recovery_id)
        self.assertEqual(recovery["backup_id"], recovery_id)

    def test_backup_refuses_to_snapshot_fallback_defaults_from_corrupt_file(self):
        self.layout_path.parent.mkdir(parents=True)
        self.layout_path.write_text("{broken", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.manager.create_backup()
        self.assertEqual(self.layout_path.read_text(encoding="utf-8"), "{broken")
        self.assertEqual(self.manager.list_backups(), [])

    def test_backup_refuses_oversized_current_layout(self):
        from desktop.layouts import MAX_LAYOUT_FILE_BYTES
        self.layout_path.parent.mkdir(parents=True)
        invalid = b"x" * (MAX_LAYOUT_FILE_BYTES + 1)
        self.layout_path.write_bytes(invalid)
        with self.assertRaises(ValueError):
            self.manager.create_backup()
        self.assertEqual(self.layout_path.read_bytes(), invalid)

    def test_restore_refuses_corrupt_current_layout_without_replacing_it(self):
        self.store.apply_profile("workspace")
        backup_id = self.manager.create_backup()
        corrupt = b"{not-json"
        self.layout_path.write_bytes(corrupt)
        with self.assertRaises(ValueError):
            self.manager.restore_backup(backup_id, confirmed=True)
        self.assertEqual(self.layout_path.read_bytes(), corrupt)

    def test_restore_refuses_symlinked_current_layout(self):
        self.store.apply_profile("workspace")
        backup_id = self.manager.create_backup()
        target = self.root / "outside.json"
        target.write_text(self.layout_path.read_text(encoding="utf-8"), encoding="utf-8")
        self.layout_path.unlink()
        try:
            self.layout_path.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolic links unavailable")
        with self.assertRaises(OSError):
            self.manager.restore_backup(backup_id, confirmed=True)
        self.assertEqual(target.read_text(encoding="utf-8"), self.layout_path.read_text(encoding="utf-8"))

    def test_tampered_backup_is_not_listed_or_restored(self):
        backup_id = self.manager.create_backup()
        (self.backups / f"{backup_id}.bak").write_text("tampered", encoding="utf-8")
        self.assertEqual(self.manager.list_backups(), [])
        with self.assertRaises(ValueError):
            self.manager.restore_backup(backup_id, confirmed=True)

    def test_manifest_symlink_is_not_followed(self):
        backup_id = self.manager.create_backup()
        manifest = self.backups / f"{backup_id}.json"
        target = self.root / "outside.json"
        target.write_bytes(manifest.read_bytes())
        manifest.unlink()
        try:
            manifest.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolic links unavailable")
        self.assertEqual(self.manager.list_backups(), [])

    def test_external_export_and_import_round_trip(self):
        self.store.apply_profile("minimal")
        backup_id = self.manager.create_backup()
        export_dir = self.root / "usb"
        export_dir.mkdir()
        self.manager.export_backup(backup_id, export_dir)
        imported_store = DesktopLayoutStore(self.root / "second-config" / "desktop-layout.json")
        imported_manager = DesktopLayoutBackupManager(imported_store, self.root / "second-state" / "backups")
        imported_id = imported_manager.import_backup(export_dir / f"{backup_id}.json")
        self.assertEqual(imported_id, backup_id)
        recovery_id = imported_manager.restore_backup(imported_id, confirmed=True)
        self.assertNotEqual(recovery_id, imported_id)
        self.assertEqual(imported_store.get()["profile"], "minimal")

    def test_export_never_overwrites_existing_files(self):
        backup_id = self.manager.create_backup()
        export_dir = self.root / "usb"
        export_dir.mkdir()
        existing = export_dir / f"{backup_id}.bak"
        existing.write_text("keep", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            self.manager.export_backup(backup_id, export_dir)
        self.assertEqual(existing.read_text(encoding="utf-8"), "keep")

    def test_import_rejects_tampered_pair_and_duplicate_ids(self):
        backup_id = self.manager.create_backup()
        export_dir = self.root / "usb"
        export_dir.mkdir()
        self.manager.export_backup(backup_id, export_dir)
        imported_manager = DesktopLayoutBackupManager(
            DesktopLayoutStore(self.root / "other-config" / "desktop-layout.json"),
            self.root / "other-state" / "backups",
        )
        pair = export_dir / f"{backup_id}.bak"
        pair.write_text("changed", encoding="utf-8")
        with self.assertRaises(ValueError):
            imported_manager.import_backup(export_dir / f"{backup_id}.json")
        pair.write_bytes((self.backups / f"{backup_id}.bak").read_bytes())
        self.assertEqual(imported_manager.import_backup(export_dir / f"{backup_id}.json"), backup_id)
        with self.assertRaises(FileExistsError):
            imported_manager.import_backup(export_dir / f"{backup_id}.json")

    def test_external_exported_files_have_private_permissions(self):
        backup_id = self.manager.create_backup()
        export_dir = self.root / "usb"
        export_dir.mkdir()
        backup_path, manifest_path = self.manager.export_backup(backup_id, export_dir)
        self.assertEqual(backup_path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(manifest_path.stat().st_mode & 0o777, 0o600)

    def test_retention_is_bounded(self):
        self.store.apply_profile("workspace")
        for _ in range(MAX_RETAINED_BACKUPS + 1):
            self.manager.create_backup()
        entries = self.manager.list_backups()
        self.assertEqual(len(entries), MAX_RETAINED_BACKUPS)
        for entry in entries:
            self.assertTrue((self.backups / f"{entry['backup_id']}.bak").is_file())
            self.assertTrue((self.backups / f"{entry['backup_id']}.json").is_file())

    def test_restore_keeps_the_selected_backup_when_retention_is_full(self):
        self.store.apply_profile("workspace")
        selected = self.manager.create_backup()
        for _ in range(MAX_RETAINED_BACKUPS - 1):
            self.manager.create_backup()
        self.store.apply_profile("minimal")
        self.manager.restore_backup(selected, confirmed=True)
        remaining = {item["backup_id"] for item in self.manager.list_backups()}
        self.assertIn(selected, remaining)
        self.assertEqual(len(remaining), MAX_RETAINED_BACKUPS)

    def test_backup_directory_symlink_is_rejected(self):
        real = self.root / "real-backups"
        real.mkdir()
        link = self.root / "linked-backups"
        try:
            link.symlink_to(real, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolic links unavailable")
        manager = DesktopLayoutBackupManager(self.store, link)
        with self.assertRaises(ValueError):
            manager.create_backup()

    def test_missing_current_layout_is_a_valid_first_run_backup(self):
        self.assertFalse(self.layout_path.exists())
        backup_id = self.manager.create_backup()
        self.assertEqual(len(self.manager.list_backups()), 1)
        self.assertEqual(self.manager.restore_backup(backup_id, confirmed=True) != backup_id, True)
        self.assertTrue(self.layout_path.exists())
        self.assertEqual(self.store.get(), DEFAULT_LAYOUT)

    def test_control_center_exposes_separate_dock_layout_recovery(self):
        root = Path(__file__).resolve().parents[1]
        controller = (root / "control_center" / "controller.py").read_text(encoding="utf-8")
        qml = (root / "control_center" / "qml" / "Main.qml").read_text(encoding="utf-8")
        self.assertIn("DesktopLayoutBackupManager(self.desktopLayout)", controller)
        self.assertIn("def createDesktopLayoutBackup(self)", controller)
        self.assertIn("def restoreDesktopLayoutBackup(self, backup_id: str)", controller)
        self.assertIn("def importDesktopLayoutBackup(self, manifest_url: str)", controller)
        self.assertIn("def exportDesktopLayoutBackup(self, backup_id: str, directory_url: str)", controller)
        self.assertIn("controlCenter.desktopLayoutBackupEntries", qml)
        self.assertIn("SAUVEGARDE DU PROFIL DE DOCK LEOS", qml)
        self.assertIn("desktopLayoutBackupRestoreDialog", qml)
        self.assertIn("FileDialog {", qml)
        self.assertIn("FolderDialog {", qml)
        self.assertIn("importDesktopLayoutBackup(selectedFile.toString())", qml)
        self.assertIn("exportDesktopLayoutBackup(", qml)

if __name__ == "__main__":
    unittest.main()
