"""LEOS Gaming Mode — Qt Quick application entry point."""

from __future__ import annotations

import subprocess
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


def _start_optional_default_apps_setup() -> None:
    """Offer approved starter apps on the first successful return to Desktop."""
    setup_script = Path("/usr/libexec/leos-default-apps-setup")
    if not setup_script.is_file():
        return
    try:
        subprocess.Popen(
            ["/usr/bin/bash", str(setup_script)],
            start_new_session=True,
            close_fds=True,
        )
    except OSError:
        # Optional software must never block the return to the KDE desktop.
        pass


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
    returned_to_desktop = {"value": False}

    def handle_desktop_request() -> None:
        returned_to_desktop["value"] = True
        app.quit()

    controller.desktopRequested.connect(handle_desktop_request)

    engine = QQmlApplicationEngine()
    context = engine.rootContext()
    context.setContextProperty("leos", controller)
    context.setContextProperty("gameLibrary", controller.library)
    context.setContextProperty("systemMonitor", controller.monitor)

    qml_file = Path(__file__).parent / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    if not engine.rootObjects():
        controller.shutdown()
        post_notification(
            "LEOS Gaming Mode indisponible",
            "L'interface Gaming n'a pas pu se charger. Le bureau KDE reste accessible.",
            "error",
        )
        return 1

    # Persist the selected mode and finish first-run onboarding only after the
    # Gaming window loaded successfully. A failed QML startup remains retryable.
    try:
        controller.settings.set_many({
            "last_mode": "gaming",
            "onboarding_complete": True,
        })
        startup_message = "L'interface Gaming a démarré."
        startup_priority = "success"
    except (OSError, ValueError, TypeError, KeyError):
        startup_message = (
            "Gaming a démarré, mais les préférences de démarrage "
            "n'ont pas pu être enregistrées."
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

    exit_code = app.exec()
    if returned_to_desktop["value"]:
        _start_optional_default_apps_setup()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
