"""Structural tests for the safe cleanup preview UI."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CleanupPreviewIntegrationTests(unittest.TestCase):
    def test_cleanup_preview_is_read_only_and_accessible(self):
        controller = (ROOT / "control_center/controller.py").read_text(encoding="utf-8")
        module = (ROOT / "control_center/cleanup.py").read_text(encoding="utf-8")
        qml = (ROOT / "control_center/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("def cleanupPreview", controller)
        self.assertIn("def scanCleanupPreview", controller)
        self.assertIn("QThreadPool.globalInstance().start(task)", controller)
        self.assertIn('{ label: "Nettoyage", page: 8 }', qml)
        self.assertIn("controlCenter.cleanupPreview.totalSize", qml)
        self.assertIn("controlCenter.scanCleanupPreview()", qml)
        self.assertIn(".cache", module)
        self.assertIn("Trash", module)
        self.assertNotIn("unlink(", module)
        self.assertNotIn("rmtree(", module)
        self.assertNotIn("remove(", module)


if __name__ == "__main__":
    unittest.main()
