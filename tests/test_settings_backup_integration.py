"""Control Center integration contract for LEOS settings recovery."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SettingsBackupIntegrationTests(unittest.TestCase):
    def test_control_center_exposes_verified_preference_backup_and_restore(self):
        controller = (ROOT / "control_center/controller.py").read_text(encoding="utf-8")
        self.assertIn("SettingsBackupManager(self.settings)", controller)
        self.assertIn("def settingsBackupSnapshot", controller)
        self.assertIn("def settingsBackupEntries", controller)
        self.assertIn("def createSettingsBackup", controller)
        self.assertIn("def exportSettingsBackup", controller)
        self.assertIn("def importSettingsBackup", controller)
        self.assertIn("def restoreSettingsBackup", controller)
        self.assertIn("def restoreLatestSettingsBackup", controller)
        self.assertIn("self.settingsBackups.restore_backup(backup_id, confirmed=True)", controller)
        self.assertIn("self._shared_settings_snapshot = self._read_shared_settings_snapshot()", controller)

    def test_restore_is_explicitly_confirmed_and_preserves_a_recovery_copy(self):
        backup = (ROOT / "leos_core/settings_backup.py").read_text(encoding="utf-8")
        settings = (ROOT / "leos_core/settings.py").read_text(encoding="utf-8")
        self.assertIn("if confirmed is not True:", backup)
        self.assertIn("recovery_backup_id = self._create_backup(preserve_backup_ids={backup_id})", backup)
        self.assertIn("def _prune_old_backups(self, *, preserve_backup_ids", backup)
        self.assertIn("self.settings.replace_all(values, confirmed=True)", backup)
        self.assertIn("if confirmed is not True:", settings)
        self.assertIn("fcntl.flock(lock.fileno(), fcntl.LOCK_EX)", settings)

    def test_control_center_has_a_separate_preferences_recovery_page(self):
        qml = (ROOT / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn('{ label: "Sauvegardes", page: 10 }', qml)
        self.assertIn("ScrollBar.vertical.policy: ScrollBar.AsNeeded", qml)
        self.assertIn('text: "SAUVEGARDES ET RÉCUPÉRATION"', qml)
        self.assertIn("controlCenter.createSettingsBackup()", qml)
        self.assertIn("controlCenter.exportSettingsBackup(", qml)
        self.assertIn("controlCenter.importSettingsBackup(", qml)
        self.assertIn("FolderDialog {", qml)
        self.assertIn("FileDialog {", qml)
        self.assertIn("fileMode: FileDialog.OpenFile", qml)
        self.assertIn("IMPORTER DEPUIS UN SUPPORT", qml)
        self.assertIn("settingsBackupExportDialog.open()", qml)
        self.assertIn("model: controlCenter.settingsBackupEntries", qml)
        self.assertIn('textRole: "label"', qml)
        self.assertIn('valueRole: "backupId"', qml)
        self.assertIn("controlCenter.restoreSettingsBackup(window.pendingSettingsBackupId, true)", qml)
        self.assertIn("settingsBackupConfirmation.open()", qml)
        self.assertIn("RESTAURER LA SÉLECTION", qml)
        self.assertIn("EXPORTER LA SÉLECTION", qml)
        self.assertIn("Les fichiers existants ne sont jamais écrasés.", qml)
        self.assertIn("Une copie de l'état actuel sera créée automatiquement", qml)
        self.assertIn("exporte une sauvegarde vers une clé USB", qml)
        self.assertIn("aucun fichier existant n'est écrasé", qml)

    def test_settings_backup_does_not_include_personal_files_or_system_operations(self):
        module = (ROOT / "leos_core/settings_backup.py").read_text(encoding="utf-8")
        self.assertIn("DEFAULTS", module)
        self.assertIn("validate_settings_values", module)
        self.assertIn("def export_backup", module)
        self.assertIn("os.O_EXCL", module)
        self.assertNotIn("subprocess", module)
        self.assertNotIn("rpm-ostree", module)
        self.assertNotIn("shutil.rmtree", module)


if __name__ == "__main__":
    unittest.main()
