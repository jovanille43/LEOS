"""Launch the LEOS Control Center."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import QUrl  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

from control_center.controller import ControlCenterController  # noqa: E402
from desktop.theme_controller import ThemeController  # noqa: E402


def main() -> int:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("LEOS Control Center")
    app.setOrganizationName("LEOS")

    controller = ControlCenterController()
    theme = ThemeController()
    engine = QQmlApplicationEngine()
    context = engine.rootContext()
    context.setContextProperty("controlCenter", controller)
    context.setContextProperty("leosTheme", theme)
    context.setContextProperty("systemMonitor", controller.monitor)
    qml_file = Path(__file__).parent / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    if not engine.rootObjects():
        theme.shutdown()
        return 1
    controller.monitor.start()
    app.aboutToQuit.connect(controller.monitor.stop)
    app.aboutToQuit.connect(theme.shutdown)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
