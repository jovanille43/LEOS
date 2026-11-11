"""Launch the LEOS Store application."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from shop.controller import StoreController


def main() -> int:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("LEOS Store")
    app.setOrganizationName("LEOS")

    store = StoreController()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("store", store)
    engine.rootContext().setContextProperty("catalogModel", store.catalog)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).parent / "qml" / "Main.qml")))
    if not engine.rootObjects():
        return 1
    store.refreshInstalled()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
