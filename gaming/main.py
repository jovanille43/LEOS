"""LEOS Gaming Mode — Qt Quick application entry point."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from backend.controller import GamingController


def main() -> int:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("LEOS Gaming")
    app.setOrganizationName("LEOS")

    controller = GamingController()
    engine = QQmlApplicationEngine()
    context = engine.rootContext()
    context.setContextProperty("leos", controller)
    context.setContextProperty("gameLibrary", controller.library)
    context.setContextProperty("systemMonitor", controller.monitor)

    qml_file = Path(__file__).parent / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    if not engine.rootObjects():
        return 1

    controller.monitor.start()
    exit_code = app.exec()
    controller.monitor.stop()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
