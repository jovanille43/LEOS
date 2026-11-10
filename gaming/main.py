"""LEOS Gaming Mode — Qt Quick application entry point."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import QUrl  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

from backend.controller import GamingController  # noqa: E402


def main() -> int:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("LEOS Gaming")
    app.setOrganizationName("LEOS")

    controller = GamingController()
    controller.desktopRequested.connect(app.quit)

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
