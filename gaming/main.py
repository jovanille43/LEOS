"""LEOS Gaming Mode — Qt Quick application entry point."""

from __future__ import annotations

import sys
import traceback
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


def _report_startup_failure() -> None:
    """Tell the user Gaming failed while keeping the KDE desktop available."""
    try:
        post_notification(
            "LEOS Gaming n'a pas pu démarrer",
            (
                "L'interface Gaming n'a pas pu être chargée. "
                "Le bureau KDE reste disponible ; consulte les journaux système "
                "pour identifier la cause."
            ),
            "error",
        )
    except Exception:
        # A broken notification service must not turn a handled startup
        # failure into a second crash or prevent the session lock being freed.
        traceback.print_exc()


def _cleanup_failed_startup(
    controller: GamingController | None,
    theme: ThemeController | None,
) -> None:
    """Stop whichever components were initialized before a startup failure."""
    if controller is not None:
        try:
            controller.shutdown()
        except Exception:
            # Preserve the original startup failure; cleanup is best-effort.
            traceback.print_exc()
    if theme is not None:
        try:
            theme.shutdown()
        except Exception:
            traceback.print_exc()


def _run_locked_session(app: QGuiApplication, _instance_lock) -> int:
    controller: GamingController | None = None
    theme: ThemeController | None = None
    try:
        controller = GamingController()
        theme = ThemeController()
        controller.desktopRequested.connect(app.quit)

        engine = QQmlApplicationEngine()
        context = engine.rootContext()
        context.setContextProperty("leos", controller)
        context.setContextProperty("leosTheme", theme)
        context.setContextProperty("gameLibrary", controller.library)
        context.setContextProperty("systemMonitor", controller.monitor)

        qml_file = Path(__file__).parent / "qml" / "Main.qml"
        engine.load(QUrl.fromLocalFile(str(qml_file)))
    except Exception:
        traceback.print_exc()
        _cleanup_failed_startup(controller, theme)
        _report_startup_failure()
        return 1

    if not engine.rootObjects():
        _cleanup_failed_startup(controller, theme)
        _report_startup_failure()
        return 1

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
