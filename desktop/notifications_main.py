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


def main() -> int:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("LEOS Notifications")
    app.setOrganizationName("LEOS")
    model = NotificationModel()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("notificationModel", model)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).parent / "qml" / "Notifications.qml")))
    if not engine.rootObjects():
        return 1
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
