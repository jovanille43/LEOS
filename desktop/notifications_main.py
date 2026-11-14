"""LEOS notification centre entry point."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from desktop.notification_model import NotificationModel
from desktop.theme_controller import ThemeController


def main() -> int:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("LEOS Notifications")
    app.setOrganizationName("LEOS")
    model = NotificationModel()
    theme = ThemeController()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("notificationModel", model)
    engine.rootContext().setContextProperty("leosTheme", theme)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).parent / "qml" / "Notifications.qml")))
    if not engine.rootObjects():
        return 1
    app.aboutToQuit.connect(theme.shutdown)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
