"""Control Center integration contract for LEOS desktop layout recovery."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DesktopLayoutBackupIntegrationTests(unittest.TestCase):
    def test_controller_uses_a_dedicated_layout_backup_manager(self):
        controller = (ROOT / "control_center/controller.py").read_text(encoding="utf-8")
        self.assertIn("from desktop.layout_backup import DesktopLayoutBackupManager", controller)
        self.assertIn("DesktopLayoutBackupManager(self.desktopLayout)", controller)
        self.assertIn("def desktopLayoutBackupSnapshot", controller)
        self.assertIn("def desktopLayoutBackupEntries", controller)
        self.assertIn("def createDesktopLayoutBackup", controller)
        self.assertIn("def exportDesktopLayoutBackup", controller)
        self.assertIn("def importDesktopLayoutBackup", controller)
        self.assertIn("def restoreDesktopLayoutBackup", controller)
        self.assertIn("self.desktopLayoutBackups.restore_backup(backup_id, confirmed=True)", controller)

    def test_ui_exposes_create_import_export_and_confirmed_restore(self):
        qml = (ROOT / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn('text: "SAUVEGARDE DES DISPOSITIONS LEOS"', qml)
        self.assertIn("controlCenter.createDesktopLayoutBackup()", qml)
        self.assertIn("controlCenter.importDesktopLayoutBackup(", qml)
        self.assertIn("controlCenter.exportDesktopLayoutBackup(", qml)
        self.assertIn("desktopLayoutBackupImportDialog.open()", qml)
        self.assertIn("desktopLayoutBackupExportDialog.open()", qml)
        self.assertIn("desktopLayoutBackupConfirmation.open()", qml)
        self.assertIn("window.pendingDesktopLayoutBackupId, true", qml)
        self.assertIn('textRole: "label"', qml)
        self.assertIn('valueRole: "backupId"', qml)

    def test_layout_preferences_and_plasma_configuration_remain_separate(self):
        qml = (ROOT / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        backup = (ROOT / "desktop/layout_backup.py").read_text(encoding="utf-8")
        self.assertIn("Les panneaux et applets KDE Plasma ne sont pas inclus", qml)
        self.assertIn("desktop-layout.json", backup)
        self.assertIn("PlasmaBackupManager", (ROOT / "control_center/controller.py").read_text(encoding="utf-8"))
        self.assertNotIn("plasma-org.kde.plasma.desktop-appletsrc", backup)

    def test_restore_requires_confirmation_and_creates_a_recovery_backup(self):
        backup = (ROOT / "desktop/layout_backup.py").read_text(encoding="utf-8")
        self.assertIn("if confirmed is not True:", backup)
        self.assertIn("recovery_backup_id = self.create_backup(preserve_backup_ids={backup_id})", backup)
        self.assertIn("self.store.replace_all(layout, confirmed=True)", backup)
        self.assertIn("self.store.validate_current_file()", backup)


if __name__ == "__main__":
    unittest.main()
