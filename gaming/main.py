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
from backend.instance_lock import acquire_instance_lock  # noqa: E402
from desktop.notifications import post_notification  # noqa: E402


def main() -> int:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("LEOS Gaming")
    app.setOrganizationName("LEOS")

    try:
        instance_lock = acquire_instance_lock("gaming")
    except OSError:
        post_notification(
            "Démarrage Gaming impossible",
            "LEOS n'a pas pu créer son verrou de session.",
            "error",
            native=False,
        )
        return 1
    if instance_lock is None:
        post_notification(
            "LEOS Gaming est déjà ouvert",
            "Une instance de Gaming Mode est déjà en cours.",
            "warning",
            native=False,
        )
        return 0

    try:
        return _run_locked_session(app, instance_lock)
    finally:
        instance_lock.unlock()


def _run_locked_session(app: QGuiApplication, _instance_lock) -> int:
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
        controller.shutdown()
        return 1

    # Persist Gaming only after its QML window loaded successfully.
    controller.settings.set("last_mode", "gaming")
    post_notification(
        "LEOS Gaming Mode",
        "L'interface Gaming a démarré.",
        "success",
        native=False,
    )
    controller.monitor.start()
    app.aboutToQuit.connect(controller.shutdown)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
