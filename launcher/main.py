"""LEOS session entry point.

KDE autostart uses --select to show the mode picker after login. Without
--select, the legacy restore path opens Gaming only when it was last selected.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from leos_core.settings import SettingsStore  # noqa: E402
from launcher.mode_manager import ModeManager  # noqa: E402
from launcher.controller import ModeSelectorController  # noqa: E402
from desktop.notifications import post_notification  # noqa: E402
from desktop.theme_controller import ThemeController  # noqa: E402


def start_gaming(ready_file: Path | None = None) -> subprocess.Popen[bytes] | None:
    gaming_entry = PROJECT_ROOT / "gaming" / "main.py"
    if not gaming_entry.is_file():
        return None
    environment = os.environ.copy()
    if ready_file is not None:
        environment["LEOS_HANDOFF_READY_FILE"] = str(ready_file)
    return subprocess.Popen(
        [sys.executable, str(gaming_entry)],
        cwd=str(gaming_entry.parent),
        env=environment,
        start_new_session=True,
        close_fds=True,
    )


def start_default_gaming_apps_setup() -> None:
    """Launch the one-time Flatpak setup without delaying the mode selector."""
    setup_script = Path("/usr/libexec/leos-default-gaming-apps-setup")
    if not setup_script.is_file():
        return
    try:
        subprocess.Popen(
            ["/usr/bin/bash", str(setup_script)],
            cwd=str(Path.home()),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
    except OSError:
        # Gaming remains usable; the bootstrap can be retried next login.
        pass


def main() -> int:
    start_default_gaming_apps_setup()
    settings = SettingsStore()
    select_mode = "--select" in sys.argv

    if not select_mode:
        if settings.get("last_mode") == "gaming":
            try:
                start_gaming()
            except OSError:
                return 1
        return 0

    from PySide6.QtCore import QUrl, QTimer
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine

    app = QGuiApplication([sys.argv[0]])
    app.setApplicationName("LEOS Mode Selector")
    app.setOrganizationName("LEOS")

    manager = ModeManager(settings)
    selector_controller = ModeSelectorController()
    theme = ThemeController(settings=settings)

    def handle_mode(mode: str) -> None:
        if mode == "gaming":
            ready_descriptor = -1
            ready_name = ""
            try:
                ready_descriptor, ready_name = tempfile.mkstemp(prefix="leos-gaming-ready-")
                os.fchmod(ready_descriptor, 0o600)
                os.close(ready_descriptor)
                ready_descriptor = -1
                ready_file = Path(ready_name)
                process = start_gaming(ready_file)
                if process is None:
                    ready_file.unlink(missing_ok=True)
                    manager.setStatus("L'application Gaming n'est pas encore installée.")
                    manager.modeLaunchFailed.emit(manager.status)
                    return
            except OSError as error:
                if ready_descriptor >= 0:
                    os.close(ready_descriptor)
                if ready_name:
                    Path(ready_name).unlink(missing_ok=True)
                message = f"Impossible de lancer Gaming Mode : {error}"
                manager.setStatus(message)
                manager.modeLaunchFailed.emit(message)
                return

            # Keep the selector's branded handoff cover visible until the
            # Gaming process confirms that its fullscreen QML window loaded.
            selected_mode["value"] = "gaming"
            deadline = time.monotonic() + 18.0
            handoff_timer = QTimer(app)
            handoff_timer.setInterval(100)

            def check_gaming_ready() -> None:
                try:
                    ready = (
                        ready_file.is_file()
                        and not ready_file.is_symlink()
                        and ready_file.stat().st_size <= 32
                        and ready_file.read_text(encoding="utf-8").strip() == "ready"
                    )
                except (OSError, UnicodeError):
                    ready = False
                if ready:
                    handoff_timer.stop()
                    ready_file.unlink(missing_ok=True)
                    app.quit()
                    return
                if process.poll() is not None or time.monotonic() >= deadline:
                    handoff_timer.stop()
                    ready_file.unlink(missing_ok=True)
                    if process.poll() is None:
                        process.terminate()
                    selected_mode["value"] = ""
                    message = (
                        "LEOS Gaming n'a pas confirmé l'affichage de son interface. "
                        "Le bureau reste accessible ; réessaie depuis le sélecteur."
                    )
                    manager.setStatus(message)
                    manager.modeLaunchFailed.emit(message)

            handoff_timer.timeout.connect(check_gaming_ready)
            handoff_timer.start()
            check_gaming_ready()
            return
        if mode == "desktop":
            selected_mode["value"] = "desktop"
            remembered = manager.rememberMode("desktop")
            post_notification(
                "LEOS Desktop Mode",
                "Le bureau KDE est sélectionné." if remembered
                else "Le bureau est actif, mais le choix de démarrage n'a pas pu être enregistré.",
                "success" if remembered else "warning",
            )
        selector_controller.completeOnboarding()
        app.quit()

    selected_mode = {"value": ""}
    manager.modeRequested.connect(handle_mode)

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("modeManager", manager)
    engine.rootContext().setContextProperty("modeSelectorController", selector_controller)
    engine.rootContext().setContextProperty("leosTheme", theme)
    app.aboutToQuit.connect(selector_controller.shutdown)
    app.aboutToQuit.connect(theme.shutdown)
    qml_file = Path(__file__).parent / "qml" / "ModeSelector.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    if not engine.rootObjects():
        selector_controller.shutdown()
        theme.shutdown()
        return 1

    app.processEvents()
    root_window = engine.rootObjects()[0]
    if not theme.themeColorsConfigured and not root_window.property("firstRunIdentityPromptVisible"):
        selector_controller.shutdown()
        theme.shutdown()
        print("LEOS first-run identity dialog did not become visible", file=sys.stderr, flush=True)
        return 1
    if not theme.themeColorsConfigured:
        print("LEOS first-run identity dialog shown successfully", flush=True)
    print("LEOS mode selector QML loaded successfully", flush=True)
    exit_code = app.exec()
    if selected_mode["value"] == "desktop":
        setup_script = Path("/usr/libexec/leos-default-apps-setup")
        if setup_script.is_file():
            try:
                subprocess.Popen(
                    ["/usr/bin/bash", str(setup_script)],
                    start_new_session=True,
                    close_fds=True,
                )
            except OSError:
                # Optional application setup must never block Desktop startup.
                pass
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
