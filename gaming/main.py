"""LEOS Gaming Mode — Qt Quick application entry point."""

from __future__ import annotations

import os
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
from desktop.theme_controller import ThemeController  # noqa: E402


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
        instance_lock.release()


def _run_locked_session(app: QGuiApplication, _instance_lock) -> int:
    controller = GamingController()
    theme = ThemeController(settings=controller.settings)
    controller.desktopRequested.connect(app.quit)

    engine = QQmlApplicationEngine()
    context = engine.rootContext()
    context.setContextProperty("leos", controller)
    context.setContextProperty("gameLibrary", controller.library)
    context.setContextProperty("systemMonitor", controller.monitor)
    context.setContextProperty("leosTheme", theme)

    qml_file = Path(__file__).parent / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    if not engine.rootObjects():
        controller.shutdown()
        theme.shutdown()
        return 1

    # Signal readiness only after the fullscreen Gaming window has rendered
    # its first frame. Loading QML alone is too early: the selector cover must
    # remain above Plasma until the compositor has a Gaming frame to display.
    ready_path = os.environ.pop("LEOS_HANDOFF_READY_FILE", "")
    if ready_path:
        root_window = engine.rootObjects()[0]

        def announce_gaming_ready() -> None:
            try:
                root_window.frameSwapped.disconnect(announce_gaming_ready)
            except (RuntimeError, TypeError):
                pass
            try:
                marker = Path(ready_path)
                if marker.is_file() and not marker.is_symlink() and marker.stat().st_size == 0:
                    descriptor = os.open(ready_path, os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0))
                    try:
                        os.write(descriptor, b"ready\\n")
                        os.fsync(descriptor)
                    finally:
                        os.close(descriptor)
            except OSError:
                # Gaming remains usable; only the selector cover may time out.
                pass

        root_window.frameSwapped.connect(announce_gaming_ready)

    print("LEOS Gaming QML loaded successfully", flush=True)

    # Persist Gaming only after its QML window loaded successfully. A
    # read-only/corrupt preference file must not prevent the session itself.
    try:
        controller.settings.set("last_mode", "gaming")
        startup_message = "L'interface Gaming a démarré."
        startup_priority = "success"
    except (OSError, ValueError, TypeError, KeyError):
        startup_message = (
            "Gaming a démarré, mais le choix du mode au prochain démarrage "
            "n'a pas pu être enregistré."
        )
        startup_priority = "warning"
    post_notification(
        "LEOS Gaming Mode",
        startup_message,
        startup_priority,
        native=False,
    )
    controller.monitor.start()
    app.aboutToQuit.connect(controller.shutdown)
    app.aboutToQuit.connect(theme.shutdown)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
