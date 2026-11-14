"""Launch the LEOS Store application."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from shop.controller import StoreController
from desktop.theme_controller import ThemeController


def main() -> int:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("LEOS Store")
    app.setOrganizationName("LEOS")

    store = None
    theme = None
    try:
        store = StoreController()
        theme = ThemeController()
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("store", store)
        engine.rootContext().setContextProperty("leosTheme", theme)
        engine.rootContext().setContextProperty("catalogModel", store.catalog)
        engine.load(QUrl.fromLocalFile(str(Path(__file__).parent / "qml" / "Main.qml")))
    except Exception:
        traceback.print_exc()
        if store is not None:
            store.shutdown()
        if theme is not None:
            theme.shutdown()
        return 1
    if not engine.rootObjects():
        store.shutdown()
        theme.shutdown()
        return 1
    store.refreshInstalled()
    app.aboutToQuit.connect(store.shutdown)
    app.aboutToQuit.connect(theme.shutdown)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
