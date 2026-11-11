"""LEOS session entry point.

KDE autostart uses --select to show the mode picker after login. Without
--select, the legacy restore path opens Gaming only when it was last selected.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from leos_core.settings import SettingsStore  # noqa: E402
from launcher.mode_manager import ModeManager  # noqa: E402
from launcher.controller import ModeSelectorController  # noqa: E402
from desktop.notifications import post_notification  # noqa: E402


def start_gaming() -> subprocess.Popen[bytes] | None:
    gaming_entry = PROJECT_ROOT / "gaming" / "main.py"
    if not gaming_entry.is_file():
        return None
    return subprocess.Popen(
        [sys.executable, str(gaming_entry)],
        cwd=str(gaming_entry.parent),
        start_new_session=True,
        close_fds=True,
    )


def main() -> int:
    settings = SettingsStore()
    select_mode = "--select" in sys.argv

    if not select_mode:
        if settings.get("last_mode") == "gaming":
            try:
                start_gaming()
            except OSError:
                return 1
        return 0

    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine

    app = QGuiApplication([sys.argv[0]])
    app.setApplicationName("LEOS Mode Selector")
    app.setOrganizationName("LEOS")

    manager = ModeManager(settings)
    selector_controller = ModeSelectorController()

    def handle_mode(mode: str) -> None:
        if mode == "gaming":
            try:
                process = start_gaming()
                if process is None:
                    manager.setStatus("L'application Gaming n'est pas encore installée.")
                    return
            except OSError as error:
                manager.setStatus(f"Impossible de lancer Gaming Mode : {error}")
                return
        manager.rememberMode(mode)
        if mode == "gaming":
            post_notification("LEOS Gaming Mode", "La session Gaming a été lancée.", "success")
        else:
            post_notification("LEOS Desktop Mode", "Le bureau KDE est sélectionné.", "success")
        app.quit()

    manager.modeRequested.connect(handle_mode)

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("modeManager", manager)
    engine.rootContext().setContextProperty("modeSelectorController", selector_controller)
    app.aboutToQuit.connect(selector_controller.shutdown)
    qml_file = Path(__file__).parent / "qml" / "ModeSelector.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    if not engine.rootObjects():
        selector_controller.shutdown()
        return 1
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
