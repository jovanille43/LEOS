"""LEOS application menu entry point."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from desktop.theme_manager import ThemeManager
from desktop.icon_provider import DesktopIconProvider
from desktop.menu_controller import ApplicationCatalog


def main() -> int:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("LEOS Menu")
    app.setOrganizationName("LEOS")
    theme_manager = ThemeManager()
    catalog = ApplicationCatalog()
    engine = QQmlApplicationEngine()
    engine.addImageProvider("desktop-icons", DesktopIconProvider())
    engine.rootContext().setContextProperty("applicationCatalog", catalog)
    engine.rootContext().setContextProperty("themeManager", theme_manager)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).parent / "qml" / "Menu.qml")))
    if not engine.rootObjects():
        theme_manager.shutdown()
        return 1
    app.aboutToQuit.connect(theme_manager.shutdown)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
