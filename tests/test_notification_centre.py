"""Tests for the LEOS notification centre integration."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class NotificationCentreIntegrationTests(unittest.TestCase):
    def test_notification_application_is_packaged(self):
        entry = (ROOT / "desktop/applications/leos-notifications.desktop").read_text(encoding="utf-8")
        recipe = (ROOT / "recipes/recipe.yml").read_text(encoding="utf-8")
        self.assertIn("notifications_main.py", entry)
        self.assertIn("src: desktop/applications/leos-notifications.desktop", recipe)

    def test_qt_model_exposes_inbox_actions(self):
        source = (ROOT / "desktop/notification_model.py").read_text(encoding="utf-8")
        for method in ("def addNotification", "def markRead", "def dismiss",
                       "def markAllRead", "def clearAll", "def unreadCount", "def refresh"):
            self.assertIn(method, source)

    def test_qml_has_read_dismiss_and_clear_controls(self):
        qml = (ROOT / "desktop/qml/Notifications.qml").read_text(encoding="utf-8")
        for action in ("notificationModel.markRead", "notificationModel.dismiss",
                       "notificationModel.clearAll", "confirmClear.open()"):
            self.assertIn(action, qml)

    def test_gaming_mode_exposes_notification_centre_access_and_unread_count(self):
        controller = (ROOT / "gaming/backend/controller.py").read_text(encoding="utf-8")
        qml = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("unreadNotificationCount", controller)
        self.assertIn("openNotificationCentre", controller)
        self.assertIn("NOTIFICATIONS", qml)
        self.assertIn("leos.openNotificationCentre()", qml)

    def test_system_notifications_are_not_claimed_as_captured(self):
        qml = (ROOT / "desktop/qml/Notifications.qml").read_text(encoding="utf-8")
        self.assertIn("Les notifications système KDE restent gérées par Plasma", qml)


if __name__ == "__main__":
    unittest.main()
