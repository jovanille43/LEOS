"""Launch the LEOS Controller Center."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import QUrl  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine
from desktop.theme_manager import ThemeManager  # noqa: E402

from controller_center.controller import ControllerCenterController  # noqa: E402


def main() -> int:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("LEOS Controller Center")
    app.setOrganizationName("LEOS")
    theme_manager = ThemeManager()
    controller = ControllerCenterController()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("controllerCenter", controller)
    engine.rootContext().setContextProperty("themeManager", theme_manager)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).parent / "qml" / "Main.qml")))
    if not engine.rootObjects():
        controller.shutdown()
        return 1
    app.aboutToQuit.connect(controller.shutdown)
    app.aboutToQuit.connect(theme_manager.shutdown)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
